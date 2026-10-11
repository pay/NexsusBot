"""Locale-aware duration text for NexsusBot.

Replaces the old hardcoded-English ``Time2Text`` in ``NexsusBot.py``. That one
built labels like ``3 Minutes`` / ``1 Minute`` with an English ``s``-plural rule,
which is wrong in most of the target languages:

  ru/ua  three plural forms (1 минута, 2 минуты, 5 минут)
  pl     three forms plus a few irregulars
  ar     six forms
  fa     two forms (singular vs everything else)
  id/en  two forms
  hi/jv  no plural marking at all, count only

Everything here degrades to English when a language has no table.
"""

# Unit names as (singular, few/dual, many, other) per language.
# Index order matches the tuple order used by ``quantize``: years, days, hours,
# minutes, seconds.
TABLES = {
    "en": (
        ("Year", "Years"), ("Day", "Days"), ("Hour", "Hours"),
        ("Minute", "Minutes"), ("Second", "Seconds"),
    ),
    "id": (
        ("Tahun", "Tahun"), ("Hari", "Hari"), ("Jam", "Jam"),
        ("Menit", "Menit"), ("Detik", "Detik"),
    ),
    "ru": (
        ("Год", "Года", "Лет"), ("День", "Дня", "Дней"),
        ("Час", "Часа", "Часов"), ("Минута", "Минуты", "Минут"),
        ("Секунда", "Секунды", "Секунд"),
    ),
    "ua": (
        ("Рік", "Роки", "Років"), ("День", "Дні", "Днів"),
        ("Година", "Години", "Годин"), ("Хвилина", "Хвилини", "Хвилин"),
        ("Секунда", "Секунди", "Секунд"),
    ),
    "de": (
        ("Jahr", "Jahre"), ("Tag", "Tage"), ("Stunde", "Stunden"),
        ("Minute", "Minuten"), ("Sekunde", "Sekunden"),
    ),
    "fr": (
        ("an", "ans"), ("jour", "jours"), ("heure", "heures"),
        ("minute", "minutes"), ("seconde", "secondes"),
    ),
    "es": (
        ("Año", "Años"), ("Día", "Días"), ("Hora", "Horas"),
        ("Minuto", "Minutos"), ("Segundo", "Segundos"),
    ),
    "pt": (
        ("Ano", "Anos"), ("Dia", "Dias"), ("Hora", "Horas"),
        ("Minuto", "Minutos"), ("Segundo", "Segundos"),
    ),
    "it": (
        ("Anno", "Anni"), ("Giorno", "Giorni"), ("Ora", "Ore"),
        ("Minuto", "Minuti"), ("Secondo", "Secondi"),
    ),
    "pl": (
        ("Rok", "Lata", "Lat"), ("Dzień", "Dni", "Dni"),
        ("Godzina", "Godziny", "Godzin"), ("Minuta", "Minuty", "Minut"),
        ("Sekunda", "Sekundy", "Sekund"),
    ),
    "ar": (
        ("سنة", "سنوات"), ("يوم", "أيام"), ("ساعة", "ساعات"),
        ("دقيقة", "دقائق"), ("ثانية", "ثواني"),
    ),
    "hi": (
        ("वर्ष", "वर्ष"), ("दिन", "दिन"), ("घंटा", "घंटे"),
        ("मिनट", "मिनट"), ("सेकंड", "सेकंड"),
    ),
    "fa": (
        ("سال", "سال"), ("روز", "روز"), ("ساعت", "ساعت"),
        ("دقیقه", "دقیقه"), ("ثانیه", "ثانیه"),
    ),
    "jv": (
        ("taun", "taun"), ("dina", "dina"), ("jam", "jam"),
        ("menit", "menit"), ("detik", "detik"),
    ),
}

# Languages where the count alone is grammatical; never append a plural form.
NO_PLURAL = frozenset(("hi", "jv"))

SECONDS_PER_UNIT = (("Year", 365.25 * 24 * 3600),
                    ("Day", 24 * 3600),
                    ("Hour", 3600),
                    ("Minute", 60),
                    ("Second", 1))


def plural_index(lang, n):
    """Which element of a unit tuple to use for count ``n``."""
    if lang == "ru" or lang == "ua":
        if n % 10 == 1 and n % 100 != 11:
            return 0
        if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            return 1
        return 2
    if lang == "pl":
        if n == 1:
            return 0
        i = n % 10
        j = n % 100
        if 2 <= i <= 4 and not 12 <= j <= 14:
            return 1
        return 2
    if lang == "ar":
        n % 100
        if n == 1:
            return 0
        if n == 2:
            return 0
        if 3 <= n <= 10:
            return 1
        if 11 <= n <= 99:
            return 2
        return 3
    if lang == "fa":
        return 0 if n == 1 else 1
    return 1 if n >= 2 else 0


def unit_names(lang):
    """Normalized 5-tuple of name-lists, or the English one for unknown langs."""
    for code in (lang, "en"):
        if code and code.lower() in TABLES:
            return TABLES[code.lower()]
    return TABLES["en"]


def _pick(table_entry, lang, n):
    """Choose a name from a 2-, 3- or 4-element unit entry."""
    if lang.lower() in NO_PLURAL:
        return table_entry[0]
    i = plural_index(lang.lower(), int(n))
    return table_entry[i] if i < len(table_entry) else table_entry[0]


def duration_text(secs, lang="en"):
    """Render ``secs`` as a localized duration, e.g. ``3 минуты``.

    Mirrors the old ``Time2Text`` output shape (space-joined, largest unit
    first, at most two non-zero components) so every existing ``%s`` call site
    keeps working unchanged.
    """
    try:
        lang = (lang or "en").lower()
    except AttributeError:
        lang = "en"
    names = unit_names(lang)

    total = float(secs)
    if total < 0:
        total = -total

    parts = []
    for idx, (_label, size) in enumerate(SECONDS_PER_UNIT):
        is_last = idx == len(SECONDS_PER_UNIT) - 1
        if is_last:
            count = int(total)
            if count < 1:
                continue
        else:
            count = int(total // size)
            if count < 1:
                continue
        parts.append("%d %s" % (count, _pick(names[idx], lang, count)))
        total -= count * size
        # The original stopped as soon as the remainder was fully consumed.
        if not total:
            break

    if not parts:
        return ""
    return " ".join(parts)