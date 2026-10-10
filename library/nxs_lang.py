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
# Hanya alias yang menunjuk kode yang benar-benar tersaji (lihat
# languages_with_reply).  Tambah alias di sini SETELAH file locale-nya
# ada - alias ke kode yang belum ada teksnya hanya jebak, karena :lang
# akan menolaknya padahal bot menawarkannya di baris bantuan.
ALIASES = {
    "indonesian": "id",
    "bahasa": "id",
    "english": "en",
    "inggris": "en",
    "russian": "ru",
    "rusia": "ru",
}

# Nama untuk pesan error/warning.
NAMES = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "ru": "Russian",
    "fi": "Finnish",
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


def is_known(lang, exp_dir="expansions"):
    """
    True kalau bahasa ini benar-benar bisa dilayani bot.

    KNOWN hanya daftar yang DIKENAL Nexsus - bukan daftar yang TERSEDIA.
    Bahasa seperti 'ru'/'fi' dikenal bot karena ada file help-nya, tapi
    belum ada file locale reply, jadi memilihnya cuma menghasilkan bahasa
    Inggris.  is_known() dipakai command `lang` untuk menolak pilihan yang
    tidak ada isinya, supaya user tidak memilih bahasa yang teksnya tidak ada.

    exp_dir: path ke folder expansions/.  Kalau None, hanya cek KNOWN.
    """
    code = normalize(lang)
    if code not in KNOWN:
        return False
    if exp_dir is None:
        return True
    # English selalu bisa dilayani: string Inggris ada langsung di AnsBase
    # tiap ekspansi dan jadi fallback loader.
    if code == "en":
        return True
    return languages_with_reply(exp_dir).count(code) > 0


def languages_with_reply(exp_dir="expansions"):
    """
    Kode bahasa yang punya setidaknya satu file ans.<lang>.json di ekspansi
    manapun.  Ini daftar yang benar-benar bisa dilayani, berbeda dari KNOWN.
    """
    found = {"en"}
    if not exp_dir or not os.path.isdir(exp_dir):
        return sorted(found)
    try:
        for name in os.listdir(exp_dir):
            sub = os.path.join(exp_dir, name)
            if not os.path.isdir(sub):
                continue
            for f in os.listdir(sub):
                if f.startswith("ans.") and f.endswith(".json"):
                    found.add(normalize(f[4:-5], default="en"))
    except OSError:
        pass
    return sorted(found)


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