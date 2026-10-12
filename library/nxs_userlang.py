#  BlackSmith mark.2 -> Nexsus Port (Python 3)
"""
nxs_userlang.py - bahasa yang dipilih user lewat command `lang`.

Kenapa modul terpisah dari users.db
-----------------------------------
`current/users.db` dipakai upstream NexsusBot (tabel `users`: chat, jid,
join_time) dan tidak boleh diubah skema - expansion lain membacanya
langsung.  Pilihan bahasa user bukan bagian dari model user upstream,
jadi disimpan di `current/userlang.db` supaya tidak mengganggu.

Yang disimpan: satu baris (chat, nick) -> kode bahasa.  Nick, bukan JID
full, supaya pilihan ikut user ketika dia ganti resource/client.

Format nilainya: kode ISO 639-1 dua huruf hasil nxs_lang.normalize().
"""

import os

import nxs_lang

DB_NAME = "userlang.db"


def db_path(base="current"):
    return os.path.join(base, DB_NAME)


def _connect(base):
    import sqlite3

    path = db_path(base)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    con = sqlite3.connect(path, timeout=5)
    con.execute(
        "CREATE TABLE IF NOT EXISTS userlang ("
        "  chat TEXT NOT NULL,"
        "  nick TEXT NOT NULL,"
        "  lang TEXT NOT NULL,"
        "  PRIMARY KEY (chat, nick))"
    )
    return con


def get_user_lang(chat, nick, base="current"):
    """
    Kode bahasa yang dipilih user, atau None kalau belum pernah memilih.

    None berarti "pakai yang lain" - command `lang` bisa dipakai untuk
    mengembalikan user ke auto-detection dengan menyimpan string kosong.
    """
    if not chat or not nick:
        return None
    try:
        con = _connect(base)
        try:
            row = con.execute(
                "SELECT lang FROM userlang WHERE chat=? AND nick=?",
                (str(chat).lower(), str(nick).lower()),
            ).fetchone()
        finally:
            con.close()
    except Exception:
        return None
    if not row:
        return None
    raw = (row[0] or "").strip()
    if not raw or raw == "auto":
        return None
    return nxs_lang.normalize(raw)


def set_user_lang(chat, nick, lang, exp_dir="expansions", base="current"):
    """
    Simpan pilihan bahasa user.  Return (ok, code_or_None).

    ok=False kalau operasinya gagal (database penuh / tidak bisa tulis) -
    pemanggil wajib memberi tahu user, jangan diamkan.
    """
    if not chat or not nick:
        return (False, None)
    chat_l = str(chat).lower()
    nick_l = str(nick).lower()
    code = None
    if lang and str(lang).strip().lower() != "auto":
        code = nxs_lang.normalize(lang)
        if not nxs_lang.is_known(code, exp_dir):
            return (False, None)
    try:
        con = _connect(base)
        try:
            con.execute(
                "INSERT OR REPLACE INTO userlang (chat, nick, lang) VALUES (?,?,?)",
                (chat_l, nick_l, code or "auto"),
            )
            con.commit()
        finally:
            con.close()
    except Exception:
        return (False, None)
    return (True, code)


def clear_user_lang(chat, nick, base="current"):
    """Hapus pilihan user supaya kembali ke deteksi otomatis."""
    if not chat or not nick:
        return False
    try:
        con = _connect(base)
        try:
            con.execute(
                "DELETE FROM userlang WHERE chat=? AND nick=?",
                (str(chat).lower(), str(nick).lower()),
            )
            con.commit()
        finally:
            con.close()
    except Exception:
        return False
    return True


def users_in_chat(chat, base="current"):
    """
    Daftar (nick, lang) untuk satu room - dipakai command `lang` tanpa argumen
    supaya user bisa lihat siapa yang sudah pakai bahasa lain.
    """
    if not chat:
        return []
    try:
        con = _connect(base)
        try:
            rows = con.execute(
                "SELECT nick, lang FROM userlang WHERE chat=? ORDER BY nick",
                (str(chat).lower(),),
            ).fetchall()
        finally:
            con.close()
    except Exception:
        return []
    return [(r[0], r[1]) for r in rows]