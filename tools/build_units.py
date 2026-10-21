#!/usr/bin/env python3
# coding: utf-8
"""
build_units.py - generate expansions/converter/units.py from the CrDesc block
in expansions/converter/code.py.

The unit display names live in the source comments:

    "watt": 1.0, # Watt; Ватт (W; Вт) !# Base
    "hour": 8766.0, # Час

Problems with parsing that at runtime:
  - ";" also appears inside parentheses: "Radiation Absorbed Dose (rad; Рад)"
  - 47 units have no English name at all (Russian only, or a bare "2^10")
  - the raw comment was printed verbatim, so users saw "Gauss; Ггаусс"

This script normalises once, offline, into a plain dict:
    UNITS[category][key] = (english, russian)
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(ROOT, "expansions", "converter", "code.py")
OUT = os.path.join(ROOT, "expansions", "converter", "units.json")

# Russian names for units whose comment has no English part.
RU_ONLY = {
    "year": "Год", "month": "Месяц", "week": "Неделя", "day": "День",
    "hour": "Час", "minute": "Минута", "second": "Секунда",
    "bit": "Бит", "byte": "Байт",
}

# Prefixes -> (English, Russian) for the units whose comment is a bare
# multiplier such as "2^10" or "10^-03".
PREFIX = [
    ("kilo",  "Kilo",  "Кило"),
    ("mega",  "Mega",  "Мега"),
    ("giga",  "Giga",  "Гига"),
    ("tera",  "Tera",  "Тера"),
    ("peta",  "Peta",  "Пета"),
    ("exa",   "Exa",   "Экса"),
    ("zetta", "Zetta", "Зетта"),
    ("yotta", "Yotta", "Йотта"),
    ("milli", "Milli", "Милли"),
    ("micro", "Micro", "Микро"),
    ("nano",  "Nano",  "Нано"),
    ("pico",  "Pico",  "Пико"),
    ("deci",  "Deci",  "Деци"),
    ("centi", "Centi", "Сенти"),
]

# Explicit names for multiplier units that do not follow the prefix rule.
EXPLICIT = {
    "kbit": ("Kilobit", "Килобит"), "mbit": ("Megabit", "Мегабит"),
    "gbit": ("Gigabit", "Гигабит"), "tbit": ("Terabit", "Терабит"),
    "pbit": ("Petabit", "Петабит"), "ebit": ("Exabit", "Эксабит"),
    "zbit": ("Zettabit", "Зеттабит"), "ybit": ("Yottabit", "Йоттабит"),
    "kbyte": ("Kilobyte", "Килобайт"), "mbyte": ("Megabyte", "Мегабайт"),
    "gbyte": ("Gigabyte", "Гигабайт"), "tbyte": ("Terabyte", "Терабайт"),
    "pbyte": ("Petabyte", "Петабайт"), "ebyte": ("Exabyte", "Эксабайт"),
    "zbyte": ("Zettabyte", "Зеттабайт"), "ybyte": ("Yottabyte", "Йоттабайт"),
    "ktesla": ("Kilotesla", "Килотесла"), "mtesla": ("Megatesla", "Мегатесла"),
    "gtesla": ("Gigatesla", "Гигатесла"), "ttesla": ("Teratesla", "Тератесла"),
    "ptesla": ("Petatesla", "Петатесла"), "etesla": ("Exatesla", "Эксатесла"),
    "ztesla": ("Zetatesla", "Зеттатесла"), "ytesla": ("Yotatesla", "Йоттатесла"),
    "militesla": ("Millitesla", "Миллитесла"),
    "microtesla": ("Microtesla", "Микротесла"),
    "nanotesla": ("Nanotesla", "Нанотесла"),
    "picotesla": ("Picotesla", "Пикотесла"),
    "kwatt": ("Kilowatt", "Киловатт"), "mwatt": ("Megawatt", "Мегаватт"),
    "gwatt": ("Gigawatt", "Гигаватт"), "twatt": ("Terawatt", "Тераватт"),
    "nanometre": ("Nanometre", "Нанометр"),
    "micrometre": ("Micrometre", "Микрометр"),
    "milimetre": ("Millimetre", "Миллиметр"),
    "centimetre": ("Centimetre", "Сантиметр"),
    "decimetre": ("Decimetre", "Дециметр"),
    "kilometre": ("Kilometre", "Километр"),
}

# Temperature units: the comment reads "from Celsius to X (Y; Z)" or
# "X (Y; Z)". The useful display name is the target unit.
TEMP_FIX = {
    "c": ("Celsius (°C)", "Цельсий (°C)"),
    "f": ("Fahrenheit (°F)", "Фаренгейт (°F)"),
    "k": ("Kelvin (K)", "Кельвин (K)"),
    "r": ("Rankine (°R)", "Ранкин (°R)"),
    "n": ("Newton (°N)", "Ньютон (°N)"),
    "de": ("Delisle (°De)", "Делиль (°De)"),
    "re": ("Réaumur (°Re)", "Реомюр (°Re)"),
    "ro": ("Römer (°Ro)", "Рёмер (°Ro)"),
}

# Typo yang ada di komentar sumber (BlackSmith asli): "Fool; Фут".
TYPO_FIX = {
    "foot": ("Foot", "Фут"),
}


def split_top(text, sep=";"):
    """Split on sep, but only at bracket depth 0."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts]


def split_names(text):
    """Pecah komentar unit jadi (english, russian).

    Pola yang ada di sumber:
      A; B                    -> ("A", "B")
      A (X; Y)                -> ("A", "Y")   nama dalam kurung = singkatan
      A (X)                   -> ("A", "A")
    ";" di dalam kurung TIDAK memisahkan nama bahasa, jadi harus
    di(split) pada kedalaman kurung nol.
    """
    parts = split_top(text)
    if len(parts) >= 2:
        return parts[0], parts[1]
    one = parts[0]
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", one)
    if m:
        head, inner = m.group(1).strip(), m.group(2)
        inner_parts = split_top(inner)
        if len(inner_parts) >= 2:
            return head, inner_parts[1]
        return head, head
    return None, one


def clean(text):
    text = text.strip()
    # drop the "!# Base" marker and any trailing parenthesised note
    if "!#" in text:
        text = text.split("!#")[0].strip()
    return text


def derive(key):
    """Nama English/Rusia untuk unit berawalan pengali."""
    if key in EXPLICIT:
        return EXPLICIT[key]
    for pre, en, ru in PREFIX:
        if key.startswith(pre) and len(key) > len(pre):
            rest = key[len(pre):]
            return (en + rest.capitalize(), ru + rest.capitalize())
    return None


def main():
    src = open(CODE, encoding="utf-8").read()
    start = src.index("CrDesc = {")
    end = src.index("\n\t}\n", start)
    block = src[start:end]

    # category -> ordered list of (key, value_expr, comment)
    cats = []
    cur = None
    for line in block.split("\n"):
        mcat = re.match(r'\t\t"([^"]+)":\s*\{', line)
        if mcat:
            cur = (mcat.group(1), [])
            cats.append(cur)
            continue
        munit = re.match(r'\t\t\t"([^"]+)":\s*(.+?),\s*#\s*(.+?)\s*$', line)
        if munit and cur:
            cur[1].append((munit.group(1), munit.group(2), munit.group(3)))

    out = {}
    problems = []
    for cat, units in cats:
        out[cat] = {}
        for key, val, comment in units:
            text = clean(comment)
            en, ru = split_names(text)
            if cat == "temperature" and key in TEMP_FIX:
                en, ru = TEMP_FIX[key]
            elif key in TYPO_FIX:
                en, ru = TYPO_FIX[key]
            elif en is None:
                if key in RU_ONLY:
                    en, ru = key.capitalize(), RU_ONLY[key]
                else:
                    d = derive(key)
                    if d:
                        en, ru = d
                    else:
                        problems.append((cat, key, text))
                        en, ru = key, text
            # nama Rusia-only dari komentar: pakai yang ada
            if ru in (ru_only := RU_ONLY.values()) and key in RU_ONLY:
                ru = RU_ONLY[key]
            out[cat][key] = [en, ru]

    if problems:
        print("unit tanpa nama:", problems, file=sys.stderr)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("ditulis: %s (%d kategori, %d unit)"
          % (os.path.relpath(OUT, ROOT), len(out),
             sum(len(v) for v in out.values())))


if __name__ == "__main__":
    main()
