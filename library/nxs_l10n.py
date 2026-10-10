#  BlackSmith mark.2 -> Nexsus Port (Python 3)
"""
LocalizationContext - pasang bahasa aktif untuk semua AnsBase sekaligus.

PORTOWANAN: paijo.ahmad@jabber.ru

Kenapa perlu
------------
16 ekspansi menulis `self.AnsBase[3]` tanpa argumen bahasa. Mengubah
semua call site jadi `self.AnsBase[3, lang]` adalah 200+ edit dan rawan
regresi. Sebagai gantinya, konteks bahasa dipasang sekali sebelum reply
dikirim, dan setiap LocalizedAnswers ikut bahasa itu.

Pakai sebagai context manager bila memungkinkan:

    with LocalizationContext(get_lang(source[1], source[2])):
        Answer(self.AnsBase[2], stype, source, disp)

Atau pasang manual bila tidak bisa memakai `with`:

    LocalizationContext.set(lang)
    try:
        ...
    finally:
        LocalizationContext.reset()

Thread-safety
-------------
Bahasa disimpan per-thread. Room handler berjalan di thread berbeda
perroom, jadi dua user dengan bahasa berbeda di dua room tidak saling
mengganggu.
"""

import threading

__all__ = ["LocalizationContext"]


class LocalizationContext(object):
    _local = threading.local()
    _registry = []
    _registry_lock = threading.Lock()

    # ── context manager ─────────────────────────────────────────

    def __init__(self, lang):
        self.lang = lang
        self._previous = None

    def __enter__(self):
        self._previous = LocalizationContext.get()
        LocalizationContext.set(self.lang)
        return self

    def __exit__(self, exc_type, exc, tb):
        LocalizationContext.set(self._previous)
        return False

    # ── API statis ──────────────────────────────────────────────

    @staticmethod
    def get():
        return getattr(LocalizationContext._local, "lang", "en")

    @staticmethod
    def set(lang):
        """Pasang bahasa untuk thread ini dan seluruh AnsBase terdaftar."""
        lang = (lang or "en").lower()
        LocalizationContext._local.lang = lang
        with LocalizationContext._registry_lock:
            targets = list(LocalizationContext._registry)
        for answers in targets:
            try:
                answers.set_lang(lang)
            except Exception:
                pass

    @staticmethod
    def reset():
        LocalizationContext.set("en")

    @staticmethod
    def register(answers):
        """Daftarkan AnsBase agar mengikuti perubahan bahasa.

        Dipanggil sekali saat ekspansi dimuat.
        """
        if answers is None:
            return
        with LocalizationContext._registry_lock:
            if answers not in LocalizationContext._registry:
                LocalizationContext._registry.append(answers)
        # Ikuti bahasa thread sekarang saat pendaftaran.
        try:
            answers.set_lang(LocalizationContext.get())
        except Exception:
            pass

    @staticmethod
    def unregister(answers):
        with LocalizationContext._registry_lock:
            if answers in LocalizationContext._registry:
                LocalizationContext._registry.remove(answers)

    @staticmethod
    def registered():
        with LocalizationContext._registry_lock:
            return list(LocalizationContext._registry)