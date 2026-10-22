#  BlackSmith mark.2 -> Nexsus Port (Python 3)
"""
nxs_locale.py - per-language reply strings for expansion AnsBase tuples.

PORTOWANAN: paijo.ahmad@jabber.ru

TUJUAN
------
Setiap expansion punya `AnsBase` berupa tuple of strings (hardcode Inggris).
Class ini membungkusnya jadi objek yang:

  1. TRANSPARAN  - `AnsBase[3]` tetap berfungsi persis seperti tuple biasa,
                   jadi 16 expansion existing tidak perlu diubah satu baris.
  2. MULTI-LANG  - kalau file locale untuk bahasa itu ada, reply memakai
                   string terjemahan; kalau tidak, jatuh ke bahasa Inggris.
  3. PER-USER    - bahasa dipilih dari `get_lang(source, nick)`.

STRUKTUR FILE LOCALE
--------------------
Locale file diletakkan di `expansions/<exp>/ans.<lang>`, format JSON:

    {
      "0": "Ответ: %s",
      "2": "Не найдено."
    }

Hanya indeks yang diisi yang dipakai; indeks lain jatuh ke default (Inggris).
Format specifier WAJIB sama dengan aslinya - kalau jumlah %s atau %d beda,
Python akan melempar TypeError saat formatting.
"""

import json
import os

__all__ = ["LocalizedAnswers"]


class LocalizedAnswers(object):
    """
    Tuple-like answers dengan dukungan bahasa.

        obj[3]         -> string untuk bahasa context terakhir
        obj[idx, "ru"] -> string untuk bahasa tertentu
        obj.defaults() -> tuple asli (untuk dump)

    BAHASA CONTEXT
    --------------
    16 ekspansi existing memanggil `self.AnsBase[idx]` tanpa argumen bahasa.
    Supaya semuanya tetap jalan tanpa edit, mode global dipakai:
    `LocalizationContext(lang)` dipasang sebelum reply dikirim, dan AnsBase
    mengikuti bahasa context itu.
    """

    def __init__(self, defaults, exp_name="", locale_dir=None):
        self._defaults = tuple(defaults)
        self._exp_name = exp_name
        self._dir = locale_dir or ""
        self._cache = {}
        self._lang = "en"

    def _path(self, lang):
        if not self._dir or not lang:
            return None
        return os.path.join(self._dir, "ans.%s.json" % lang.lower())

    def load(self, lang):
        """Muat tabel locale untuk satu bahasa. Cache per bahasa."""
        lang = (lang or "en").lower()
        if lang in self._cache:
            return self._cache[lang]
        table = {}
        path = self._path(lang)
        if path and os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    raw = json.load(fh)
                for k, v in raw.items():
                    idx = int(k)
                    if 0 <= idx < len(self._defaults) and isinstance(v, str):
                        table[idx] = v
            except Exception:
                # Locale rusak tidak boleh menjatuhkan bot - reply saja
                # dalam bahasa Inggris.
                table = {}
        self._cache[lang] = table
        return table

    def set_lang(self, lang):
        """Pasang bahasa context aktif."""
        self._lang = (lang or "en").lower()

    def _thread_lang(self):
        """Bahasa milik thread pemanggil, atau None.

        Penting: instance LocalizedAnswers itu SHARED antar thread (satu
        per expansion), jadi `self._lang` cuma nyimpan bahasa terakhir
        yang di-set. Kalau dua user dengan bahasa berbeda command-nya
        jalan paralel, satu bisa dapat string milik yang lain.

        Karena itu pembacaan string selalu memakai bahasa thread
        pemanggil dulu (thread-local), dan `self._lang` cuma fallback
        untuk pemanggil yang memang tidak memasang bahasa.
        """
        try:
            from nxs_l10n import LocalizationContext
            return LocalizationContext.get_explicit()
        except Exception:
            return None

    def current_lang(self):
        """Bahasa aktif untuk pemanggil (thread-local, fallback shared)."""
        lang = self._thread_lang()
        return (lang or self._lang or "en").lower()

    def pick(self, idx, lang=None):
        """String untuk indeks tertentu pada bahasa tertentu."""
        i = self._resolve(idx)
        if i is None:
            raise IndexError("AnsBase index out of range")
        if lang is None:
            lang = self._thread_lang() or self._lang
        table = self.load(lang)
        return table.get(i, self._defaults[i])

    def _resolve(self, idx):
        if idx < 0:
            idx += len(self._defaults)
        if idx < 0 or idx >= len(self._defaults):
            return None
        return idx

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._defaults[idx]
        i = self._resolve(idx)
        if i is None:
            raise IndexError("AnsBase index out of range")
        lang = self._thread_lang() or self._lang
        table = self.load(lang)
        return table.get(i, self._defaults[i])

    def __len__(self):
        return len(self._defaults)

    def __iter__(self):
        return iter(self._defaults)

    def __contains__(self, item):
        return item in self._defaults

    def index(self, item):
        return self._defaults.index(item)

    def count(self, item):
        return self._defaults.count(item)

    def defaults(self):
        """Tuple asli - dipakai dump/serialisasi."""
        return self._defaults

    def languages(self):
        """Bahasa yang punya file locale untuk ekspansi ini."""
        if not self._dir or not os.path.isdir(self._dir):
            return []
        found = []
        for name in os.listdir(self._dir):
            if name.startswith("ans.") and name.endswith(".json"):
                found.append(name[4:-5])
        return sorted(found)

    def __repr__(self):
        return ("<LocalizedAnswers %s lang=%s len=%d>"
                % (self._exp_name or "?", self._lang, len(self._defaults)))