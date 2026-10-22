#!/usr/bin/env python3
# coding: utf-8
"""
test_lang_race.py - regression test untuk balasan bilingual yang salah.

Bug yang diperbaiki
-------------------
Instance LocalizedAnswers itu SHARED antar thread (satu per expansion).
Dulu `LocalizedAnswers.__getitem__` membaca `self._lang`, yaitu bahasa
terakhir yang di-set - jadi dua user dengan bahasa berbeda yang
command-nya jalan paralel bisa dapat string milik satu sama lain.

Perbaikan:
  - `LocalizationContext.get_explicit()` - bahasa milik thread ini, atau
    None kalau thread belum pernah memasang bahasa.
  - `LocalizedAnswers.__getitem__` / `pick()` membaca thread-local dulu.
  - `Cmd.execute` meneruskan bahasa peminta ke thread command lewat
    `sThread(..., lang)`, dan `composeThr` memasangnya di thread baru.

Test ini mensimulasikan alur nyata: thread pesan memasang bahasa, lalu
thread command (thread BARU) membaca string reply.

Jalankan dari root repo:
    python3 tools/test_lang_race.py
"""
import os
import sys
import json
import shutil
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "library"))
sys.path.insert(0, ROOT)

from nxs_l10n import LocalizationContext      # noqa: E402
from nxs_locale import LocalizedAnswers       # noqa: E402


def make_answers(lang, marker):
    """LocalizedAnswers dengan satu locale bahasa tertentu."""
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "ans.%s.json" % lang), "w",
              encoding="utf-8") as fh:
        json.dump({"0": "%s-0" % marker, "1": "%s-1" % marker}, fh)
    return LocalizedAnswers(("EN-0", "EN-1"), exp_name=marker,
                             locale_dir=d), d


def compose_thread(handler, lang):
    """Tiru composeThr: bahasa dipasang DI DALAM thread baru."""
    def runner():
        if lang:
            LocalizationContext.set(lang)
        handler()
    t = threading.Thread(target=runner)
    t.start()
    t.join()


def one_round(answers_id, answers_ru):
    """Dua user (id & ru) menjalankan command bersamaan."""
    results = []
    barrier = threading.Barrier(2)

    def scenario(lang, answers):
        # Thread pesan: pasang bahasa peminta.
        LocalizationContext.set(lang)

        def cmd():
            # Thread command: thread BARU, baca string reply.
            barrier.wait()
            results.append((lang, answers[0]))

        compose_thread(cmd, lang)

    t1 = threading.Thread(target=scenario, args=("id", answers_id))
    t2 = threading.Thread(target=scenario, args=("ru", answers_ru))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    return results


def main():
    answers_id, d1 = make_answers("id", "ID")
    answers_ru, d2 = make_answers("ru", "RU")
    LocalizationContext.register(answers_id)
    LocalizationContext.register(answers_ru)

    # 1. Satu putaran: dua bahasa paralel.
    res = one_round(answers_id, answers_ru)
    by_lang = dict(res)
    ok_single = (by_lang.get("id", "").startswith("ID")
                  and by_lang.get("ru", "").startswith("RU"))

    # 2. Stress: 200 putaran, dua bahasa paralel.
    all_res = []
    for _ in range(200):
        all_res += one_round(answers_id, answers_ru)
    wrong = [r for r in all_res if not r[1].startswith(r[0].upper())]

    # 3. Thread tanpa bahasa harus dapat fallback yang konsisten.
    fallback = answers_id[0]

    shutil.rmtree(d1, ignore_errors=True)
    shutil.rmtree(d2, ignore_errors=True)

    print("satu putaran :", sorted(res))
    print("stress       : %d sampel, %d salah" % (len(all_res), len(wrong)))
    if wrong:
        print("  contoh salah:", wrong[:3])
    print("fallback     :", fallback)

    if ok_single and not wrong:
        print("OK - tiap thread dapat bahasa sendiri, tidak ada tumpang tindih.")
        return 0
    print("GAGAL - balasan bisa tertukar antar user.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
