# coding: utf-8
# Plugin: update
# Author: paijo.ahmad@jabber.ru
# NexsusBot Expansion — update kode bot dari git repository
# exp_name = "update" # /code.py v.1.0

import subprocess
import os as _os
import threading

BOT_ROOT = _os.path.dirname(_os.path.abspath(ExpsDir))


def _run_git(args, timeout=30):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=BOT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        return result.returncode, out
    except Exception as e:
        return -1, str(e)


class expansion_temp(expansion):

    def __init__(self, name):
        expansion.__init__(self, name)

    AnsBase = (
        "Mengecek update dari git...",                                        # 0
        "Sudah versi terbaru, tidak ada update baru.",                         # 1
        "Update tersedia (belum ditarik):\n%s\n\nJalankan 'update pull'.",     # 2
        "Menarik update dari git...",                                         # 3
        "Update berhasil ditarik:\n%s\n\n"
        "Jalankan 'update restart' untuk menerapkan (bot akan restart).",     # 4
        "Gagal update:\n%s",                                                  # 5
        "Bot akan restart sekarang untuk menerapkan update...",               # 6
        "Git status:\n%s",                                                    # 7
        "Bukan git repository, atau git tidak tersedia di device ini.",       # 8
        "Ada perubahan lokal yang belum di-commit -- update DIBATALKAN demi "
        "keamanan (supaya tidak menimpa perubahan yang belum disimpan).\n"
        "Jalankan 'update status' untuk detail, commit/stash dulu manual, "
        "baru ulangi 'update pull'.",                                         # 9
        "Usage: update [check|pull|restart|status]",                          # 10
    )

    def _is_git_repo(self):
        code, _ = _run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0

    def command_update(self, stype, source, body, disp):
        if not self._is_git_repo():
            Answer(self.AnsBase[8], stype, source, disp)
            return

        arg = (body or "").strip().lower()

        if arg == "status":
            code, out = _run_git(["status", "--short", "--branch"])
            Answer(self.AnsBase[7] % (out or "(bersih, tidak ada perubahan)"), stype, source, disp)
            return

        if arg == "restart":
            Answer(self.AnsBase[6], stype, source, disp)
            # fix: delay sedikit supaya pesan "akan restart" kekirim dulu
            # sebelum proses benar-benar exit & replace dirinya sendiri.
            threading.Timer(1.5, lambda: sys_exit("Restart setelah update (manual)")).start()
            return

        if arg in ("check", ""):
            Answer(self.AnsBase[0], stype, source, disp)
            threading.Thread(target=self._check_update, args=(stype, source, disp), daemon=True).start()
            return

        if arg == "pull":
            threading.Thread(target=self._do_pull, args=(stype, source, disp), daemon=True).start()
            return

        Answer(self.AnsBase[10], stype, source, disp)

    def _check_update(self, stype, source, disp):
        _run_git(["fetch"])
        code, out = _run_git(["log", "HEAD..origin/HEAD", "--oneline"])
        if code != 0:
            # fallback kalau symbolic ref origin/HEAD belum ke-set, coba origin/main
            code, out = _run_git(["log", "HEAD..origin/main", "--oneline"])
        if not out:
            Answer(self.AnsBase[1], stype, source, disp)
        else:
            Answer(self.AnsBase[2] % out, stype, source, disp)

    def _do_pull(self, stype, source, disp):
        # fix: cegah pull kalau ada perubahan lokal belum di-commit --
        # git pull bisa gagal aneh (conflict) atau berpotensi bikin state
        # kerja jadi campur aduk kalau ada uncommitted changes.
        code, out = _run_git(["status", "--porcelain"])
        if out.strip():
            Answer(self.AnsBase[9], stype, source, disp)
            return

        Answer(self.AnsBase[3], stype, source, disp)
        code, out = _run_git(["pull", "--ff-only"])
        if code == 0:
            Answer(self.AnsBase[4] % (out or "(sudah up to date)"), stype, source, disp)
        else:
            Answer(self.AnsBase[5] % out, stype, source, disp)

    commands = (
        # access 8 = God-level saja -- command ini bisa jalankan git &
        # restart proses bot, jangan dibuka untuk level akses lebih rendah.
        (command_update, "update", 8,),
    )
