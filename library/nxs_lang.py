#  BlackSmith mark.2 -> Nexsus Port (Python 3)
"""
nxs_lang.py - daftar bahasa yang dikenal bot.

PORTOWANAN: paijo.ahmad@jabber.ru

Kenapa modul ini ada
--------------------
`DefLANG` di NexsusBot.py di-parse dengan `.upper()[:2]`, jadi nilai config
hanya dua huruf pertama.  Consequences:

  * `LANG = ID`      -> "ID"  (bagus)
  * `LANG = Indonesian` -> "IN"  ( salah - "IN" bukan kode bahasa ISO 639-1)

Presence stanza XMPP juga mengirim `lang` sebagai tag seperti `id`, `en-gb`,
`ru`.  Modul ini dipakai untuk:

  1. MEMVALIDASI nilai config: kalau user tulis "Indonesian", beri peringatan
     dan tunjukkan kode yang benar, bukan diam-diam pakai "IN".
  2. NORMALISKAN tag bahasa dari presence: `pt-br` -> `pt`.
  3. MENYEDIAKAN daftar bahasa yang punya dukungan reply (dari file locale).
"""

import os

# ── Kode yang tahu Nexsus ────────────────────────────────────────
# Dua huruf (ISO 639-1).  Nilai di sini HANYA kode yang sah; daftar bahasa
# yang punya file locale dihitung terpisah di supported_reply_languages().

KNOWN = (
    "en",   # English
    "id",   # Bahasa Indonesia
    "ru",   # Russian
    "fi",   # Finnish
)

# Nama yang sering diketik orang tapi bukan kode bahasa.
ALIASES = {
    "indonesian": "id",
    "bahasa": "id",
    "melayu": "ms",
    "english": "en",
    "inggris": "en",
    "russian": "ru",
    "rusia": "ru",
    "finnish": "fi",
    "finland": "fi",
}

# Nama untuk pesan error/warning.
NAMES = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "ru": "Russian",
    "fi": "Finnish",
    "ms": "Bahasa Melayu",
}


def normalize(tag, default="en"):
    """
    Bersihkan tag bahasa dari presence atau config.

        "id"      -> "id"
        "pt-BR"   -> "pt"
        "en_US"   -> "en"
        "Indonesian" -> "id"   (lewat ALIASES)
        None      -> default
    """
    if not tag:
        return default
    t = str(tag).strip().lower()
    if not t:
        return default
    # Tag bahasa kadang punya prefiks region atau private-use, buang saja.
    if "-" in t:
        t = t.replace("-", "_").split("_")[0]
    if t in ALIASES:
        return ALIASES[t]
    # Hanya dua huruf awal dianggap kode bahasa.
    if len(t) >= 2 and t[:2].isalpha():
        return t[:2]
    return default


def is_known(lang):
    return normalize(lang) in KNOWN


def describe(lang):
    """Nama bahasa yang enak dibaca, atau kodenya apa adanya."""
    code = normalize(lang)
    return NAMES.get(code, code)


def supported_reply_languages(exp_dir):
    """
    Bahasa yang punya file locale reply untuk satu ekspansi.

    exp_dir: path ke expansions/<exp>/
    """
    if not exp_dir or not os.path.isdir(exp_dir):
        return []
    found = []
    for name in os.listdir(exp_dir):
        if name.startswith("ans.") and name.endswith(".json"):
            found.append(name[4:-5].lower())
    return sorted(set(found))


def warn_if_unknown(lang):
    """
    Pesan peringatan untuk nilai config yang tidak dikenali, atau None
    kalau kodenya valid.  Bot harus tetap jalan - pemanggil cukup
    _Log() hasilnya sebagai warning.
    """
    raw = (lang or "").strip()
    if not raw:
        return None
    code = normalize(raw)
    if code in KNOWN:
        return None
    hint = ALIASES.get(raw.lower())
    if hint:
        return ("LANG=%r bukan kode bahasa; mungkin maksudnya %r"
                % (raw, hint))
    return ("LANG=%r tidak dikenal. Kode yang didukung: %s"
            % (raw, ", ".join(KNOWN)))