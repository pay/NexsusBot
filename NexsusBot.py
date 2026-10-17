#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Porting Python3 by: paijo.ahmad@jabber.ru

# ╔══════════════════════════════════════════════════════════════╗
# ║              NEXSUS SAFETY  —  XMPP Core Engine                 ║
# ║         Turunan dari BlackSmith mark.2 (WitcherGeralt)      ║
# ║                  (c) 2026 Nexsus Project                     ║
# ║         XMPP: slixmpp (Python 3 stable)                     ║
# ╚══════════════════════════════════════════════════════════════╝

# ── Dependencies ───────────────────────────────────────────────
# pip install slixmpp
#
# slixmpp adalah library XMPP Python 3 yang aktif dikembangkan,
# mendukung: SASL, TLS, MUC, Roster, Caps, Ping, Version, dll.
# Repo: https://codeberg.org/poezio/slixmpp
# ──────────────────────────────────────────────────────────────

# ── Imports ────────────────────────────────────────────────────

import sys
import os
import gc
import time
import asyncio
import socket
import threading
import traceback
import logging
import logging.handlers
import sqlite3
import configparser

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from types          import SimpleNamespace
from traceback      import print_exc as exc_info__
from random         import randrange, choice
from re             import compile as compile__
from argparse       import ArgumentParser
from concurrent.futures import Future

# ── slixmpp imports ────────────────────────────────────────────

try:
    import slixmpp
    from slixmpp                    import ClientXMPP, JID
    from slixmpp.exceptions         import IqError, IqTimeout
    from slixmpp.xmlstream          import ET
    from slixmpp.xmlstream.stanzabase import StanzaBase
    import slixmpp.plugins.xep_0045 as xep_0045_module  # MUC
except ImportError:
    print("[NEXUS] ERROR: slixmpp not found. Install with: pip install slixmpp")
    sys.exit(1)

# Namespace constants (mengganti xmpp.NS_* dari xmpppy)
class NS:
    MUC          = "http://jabber.org/protocol/muc"
    MUC_USER     = "http://jabber.org/protocol/muc#user"
    MUC_ADMIN    = "http://jabber.org/protocol/muc#admin"
    MUC_OWNER    = "http://jabber.org/protocol/muc#owner"
    CAPS         = "http://jabber.org/protocol/caps"
    VERSION      = "jabber:iq:version"
    TIME         = "jabber:iq:time"
    URN_TIME     = "urn:xmpp:time"
    LAST         = "jabber:iq:last"
    PING         = "urn:ietf:params:xml:ns:xmpp-session"
    DISCO_INFO   = "http://jabber.org/protocol/disco#info"
    RECEIPTS     = "urn:xmpp:receipts"
    ROSTER       = "jabber:iq:roster"
    SASL         = "urn:ietf:params:xml:ns:xmpp-sasl"
    TLS          = "urn:ietf:params:xml:ns:xmpp-tls"
    PRESENCE     = "presence"
    MESSAGE      = "message"
    IQ           = "iq"

# ── Path Setup ─────────────────────────────────────────────────

NxCore = getattr(sys.modules["__main__"], "__file__", None)
if NxCore:
    NxCore  = os.path.abspath(NxCore)
    NxRoot  = os.path.dirname(NxCore)
    if NxRoot:
        os.chdir(NxRoot)
else:
    NxRoot  = os.getcwd()
    NxCore  = ""

LibDir = "library"
sys.path.insert(0, LibDir)

# Peringatan LANG yang tidak dikenal; diisi load_config().
_lang_warn = None

# ── Localization ───────────────────────────────────────────────
# Bungkus AnsBase tuple polos jadi LocalizedAnswers supaya reply bisa
# memakai string per bahasa tanpa mengubah satu baris pun di 16 ekspansi.
# Import gagal (mis. library/ hilang) tidak boleh menjatuhkan bot:
# _wrap_answers() akan mengembalikan tuple apa adanya.
try:
    from nxs_locale import LocalizedAnswers
    from nxs_l10n import LocalizationContext
    import nxs_lang
    import nxs_userlang
except Exception:                      # noqa: BLE001 - degradasi ke non-lokalisasi
    LocalizedAnswers  = None
    LocalizationContext = None
    nxs_lang          = None
    nxs_userlang      = None


def _wrap_answers(answers, exp_name, exp_dir):
    """Tuple -> LocalizedAnswers, kalau infra lokalisasi tersedia."""
    if LocalizedAnswers is None or not answers:
        return answers
    try:
        wrapped = LocalizedAnswers(answers, exp_name=exp_name,
                                    locale_dir=exp_dir)
    except Exception:
        return answers
    try:
        LocalizationContext.register(wrapped)
    except Exception:
        pass
    return wrapped

# ── Argument Parser ────────────────────────────────────────────

argParser = ArgumentParser(description="Nexsus Safety XMPP Engine")
argParser.add_argument("-s", "--static",     help="Static folder",    default="static")
argParser.add_argument("-d", "--dynamic",    help="Dynamic folder",   default="current")
argParser.add_argument("-e", "--expansions", help="Expansions folder", default="expansions")
args = argParser.parse_args()

# ── Logging Manager ────────────────────────────────────────────

_LOG_LEVELS = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "OFF":      logging.CRITICAL + 10,
}


class LogManager:
    """
    Satu-satunya pintu log di bot ini.  Seluruh setelan diambil dari
    section [LOGGING] di static/config.ini:

        LEVEL         ambang yang ditulis ke file (dan ke console)
        FILE          path file log; kosong / NONE = tidak ada file log
        CONSOLE       True = log ikut tampil di terminal
        MAX_BYTES     batas ukuran per file sebelum di-rotate
        BACKUP_COUNT  jumlah file rotasi yang disimpan
        FORMAT / DATE_FORMAT   pola baris log

    Semua nilai opsional: section hilang atau option tidak ada → default
    dipakai, bot tetap jalan.  Dipanggil sekali di import dengan default,
    lalu dipanggil ulang dari load_config() setelah config terbaca.
    """

    DEFAULTS = {
        "LEVEL":        "INFO",
        "FILE_LEVEL":   "DEBUG",
        "FILE":         "nexsus.log",
        "CONSOLE":      "False",
        "MAX_BYTES":    str(2 * 1024 * 1024),
        "BACKUP_COUNT": "3",
        "FORMAT":       "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        "DATE_FORMAT":  "%d.%m.%Y %H:%M:%S",
    }

    class SlixmppFilter(logging.Filter):
        # "Unknown stanza interface" = warning dari slixmpp yang tidak ada
        # aksi yang bisa diambil dan sudah di-handle via XML fallback parse.
        _suppress = ("Unknown stanza interface:",)

        def filter(self, record):
            return not any(s in record.getMessage() for s in self._suppress)

    def __init__(self, name="nexsus"):
        self.name    = name
        self.logger  = logging.getLogger(name)
        self.console = None
        self.file    = None
        self._owned  = []
        self.settings  = dict(self.DEFAULTS)
        self.level_name = self.DEFAULTS["LEVEL"]
        self.configure()

    # ── internal ───────────────────────────────────────────────

    @staticmethod
    def _bool(value, fallback=False):
        try:
            return configparser.ConfigParser.BOOLEAN_STATES[str(value).strip().lower()]
        except KeyError:
            return fallback

    def _clear(self):
        # Hanya copot handler milik sendiri — handler root milik library lain
        # (slixmpp, asyncio) tidak boleh ikut hilang.
        root = logging.getLogger()
        for handler in self._owned:
            for target in (self.logger, root):
                if handler in target.handlers:
                    target.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
        self._owned    = []
        self.console   = None
        self.file      = None

    # ── public ─────────────────────────────────────────────────

    def configure(self, con=None, defaults=None):
        """(Re)pasang handler sesuai [LOGGING].  con=None → pakai default."""
        values = dict(self.DEFAULTS)
        if defaults:
            values.update(defaults)
        if con is not None:
            for key in values:
                try:
                    values[key] = con.get("LOGGING", key, fallback=values[key])
                except Exception:
                    pass
        self.settings = {k: str(v) for k, v in values.items()}

        self._clear()

        raw_level = self.settings["LEVEL"].strip().upper()
        if raw_level in _LOG_LEVELS:
            level = _LOG_LEVELS[raw_level]
            self.level_name = raw_level
        else:
            # Level ngawur di config = error config, bukan error fatal.
            # Pakai DEBUG supaya isinya tetap kelihatan, dan sebut di
            # ringkasan startup kalau nilai aslinya ditolak.
            level          = logging.DEBUG
            self.level_name = "%s (unknown, pakai DEBUG)" % (
                raw_level or "kosong")
        fmt = logging.Formatter(self.settings["FORMAT"],
                                 self.settings["DATE_FORMAT"])

        # FILE_LEVEL boleh lebih rendah dari LEVEL: file log jadi lengkap,
        # terminal tetap ringkas.  Logger harus di level terendah supaya
        # record yang dilewatkan console tetap sampai ke file handler.
        raw_file_level = self.settings["FILE_LEVEL"].strip().upper()
        file_level = (_LOG_LEVELS.get(raw_file_level) or level)

        self.logger.setLevel(min(level, file_level))
        self.logger.propagate = False

        if self._bool(self.settings["CONSOLE"]):
            console = logging.StreamHandler(sys.stderr)
            console.setLevel(level)
            console.setFormatter(fmt)
            self.console = console
            self._owned.append(console)
            self.logger.addHandler(console)

        path = self.settings["FILE"].strip()
        if path and path.upper() not in ("NONE", "OFF", "-"):
            try:
                max_bytes = int(float(self.settings["MAX_BYTES"]))
                backups   = int(float(self.settings["BACKUP_COUNT"]))
            except (TypeError, ValueError):
                max_bytes, backups = int(self.DEFAULTS["MAX_BYTES"]), 3
            if max_bytes > 0:
                try:
                    handler = logging.handlers.RotatingFileHandler(
                        path, maxBytes=max_bytes, backupCount=backups,
                        encoding="utf-8")
                except OSError:
                    handler = logging.handlers.FileHandler(path, encoding="utf-8")
                handler.setLevel(file_level)
                handler.setFormatter(fmt)
                self.file   = handler
                self._owned.append(handler)
                self.logger.addHandler(handler)

        # Root logger: bot ini TIDAK_PAYA lihat log library.  Tanpa handler
        # sama sekali, library akan jatuh ke logging.lastResort yang
        # mencetak WARNING ke stderr — persis perilaku yang unattractive
        # ini sebelumnya.  Filter pun harus nempel di HANDLER, bukan di
        # logger: filter di logger cuma menyaring record yang dilog
        # langsung ke logger itu, record dari slixmpp tetap lewat apa adanya.
        root = logging.getLogger()
        if not root.handlers:
            quiet = logging.StreamHandler(sys.stderr)
            quiet.setLevel(logging.WARNING)
            quiet.setFormatter(fmt)
            root.addHandler(quiet)
            self._owned.append(quiet)
        for handler in root.handlers:
            if not any(isinstance(f, LogManager.SlixmppFilter)
                       for f in handler.filters):
                handler.addFilter(LogManager.SlixmppFilter())

        return self.settings

    def describe(self):
        """Ringkasan singkat buat Cetak ke terminal saat start."""
        where = self.settings["FILE"].strip() or "off"
        if self.file:
            where += " (rotate %s x %s)" % (
                self.settings["BACKUP_COUNT"], self.settings["MAX_BYTES"])
        elif self.settings["FILE"].strip().upper() not in ("NONE", "OFF", "-"):
            where += " (unavailable)"
        return "%s → file: %s, console: %s" % (
            self.level_name, where, "on" if self.console else "off")

    def log(self, level, text):
        try:
            self.logger.log(level, text)
        except Exception:
            pass

    def error(self, text):
        self.log(logging.ERROR, text)


logMgr  = LogManager()
logger  = logMgr.logger   # alias supaya call site lama tetap jalan

# ── ANSI Colors ────────────────────────────────────────────────

color0 = "\033[0m"          # reset
color1 = "\033[33m"         # kuning  — warning
color2 = "\033[31;1m"       # merah   — error
color3 = "\033[32m"         # hijau   — ok
color4 = "\033[34;1m"       # biru    — info
color5 = "\033[36m"         # cyan    — header/divider
color6 = "\033[90m"         # abu-abu — detail kecil

def _term_width():
    """Lebar terminal saat ini, dengan batas aman untuk HP/Termux."""
    try:
        import shutil as _shutil
        w = _shutil.get_terminal_size(fallback=(50, 24)).columns
    except Exception:
        w = 50
    # Termux portrait biasanya 32-46 kolom, desktop 80+.
    return max(32, min(w, 70))

_TW = _term_width()  # lebar baris (termasuk 2 spasi indent), auto-detect


def _hr(char="\u2500"):
    """Garis horizontal selebar layar — flat, tanpa karakter kotak."""
    return char * _TW


def _Log(text, level):
    """Tulis ke file log (tanpa warna). Kalau logging gagal, jangan ganggu output."""
    logMgr.log(level, text)


# ── Pay-style output ───────────────────────────────────────────
# Semua output lewat logger dengan satu format global, persis seperti
# `~/pay/app.py` (basicConfig level=INFO + format asctime/name/level/message).
# Tidak ada print(), banner, emoji, warna, atau divider.


def Print(text, color=None):
    _Log(text, logging.INFO)


def PrintOK(text):
    _Log(text, logging.INFO)


def PrintWarn(text):
    _Log(text, logging.WARNING)


def PrintErr(text):
    _Log(text, logging.ERROR)


def PrintInfo(text):
    _Log(text, logging.INFO)


def PrintDivider():
    """No-op — pay-style tidak memakai garis pemisah."""
    return


def PrintHeader(title):
    """No-op — pay-style tidak memakai section header."""
    return


def PrintSection(title):
    """Alias kompatibilitas — section header flat."""
    PrintHeader(title)


# ── Product Identity ───────────────────────────────────────────

(NxMark, NxVer, NxRev) = (1, 2, 0)
ProdName   = "Nexsus Serve"
ProdCore   = "BlackSmith-M.2"
ProdVer    = "%d.%d.%d Core:%s" % (NxMark, NxVer, NxRev, ProdCore)
Caps       = "https://nexsus-bot.xmpp/core"
CapsVer    = "%d.%d" % (NxMark, NxVer)
FullName   = "%s %s" % (ProdName, ProdVer)

BotOS, NxPid = os.name, os.getpid()
OSList = SimpleNamespace(
    windows = (BotOS == "nt"),
    posix   = (BotOS == "posix")
)


def _print_banner():
    """Pay-style: satu baris identitas, lewat logger."""
    _Log("%s %d.%d.%d | %s | pid %d"
         % (ProdName, NxMark, NxVer, NxRev, GenDisp, NxPid), logging.INFO)
    _Log("language: %s" % (nxs_lang.describe(DefLANG)
                            if nxs_lang else DefLANG), logging.INFO)
    if _lang_warn:
        PrintWarn(_lang_warn)


def _print_startup_summary(ok_count, err_count):
    """Pay-style: satu baris ringkasan, lewat logger."""
    n_cmds    = len([c for c in Cmds.values() if c.isAvailable])
    n_rooms   = len(Chats)
    n_clients = sum(1 for c in Clients.values() if c.isConnected())
    n_total   = len(Clients)

    _Log("%d expansions, %d commands, %d room(s), %d/%d clients"
         % (ok_count, n_cmds, n_rooms, n_clients, n_total), logging.INFO)



sBase = (
    "chat",        # 0
    "groupchat",   # 1
    "normal",      # 2
    "available",   # 3
    "unavailable", # 4
    "subscribe",   # 5
    "answer",      # 6
    "error",       # 7
    "result",      # 8
    "set",         # 9
    "get",         # 10
    "jid",         # 11
    "nick",        # 12
    "dispatch",    # 13
    "request",     # 14
    "received",    # 15
    "ping",        # 16
    "time",        # 17
    "query"        # 18
)

aRoles = (
    "affiliation", # 0
    "outcast",     # 1
    "none",        # 2
    "member",      # 3
    "admin",       # 4
    "owner",       # 5
    "role",        # 6
    "visitor",     # 7
    "participant", # 8
    "moderator"    # 9
)

sList = ("chat", "away", "xa", "dnd")

aDesc = {
    "owner":       3,
    "moderator":   3,
    "admin":       2,
    "participant": 1,
    "member":      1
}

sCodesDesc = {
    "301": "has-been-banned",
    "303": "nick-changed",
    "307": "has-been-kicked",
    "407": "members-only"
}

eCodesDesc = {
    "302": "redirect",
    "400": "unexpected-request",
    "401": "not-authorized",
    "402": "payment-required",
    "403": "forbidden",
    "404": "remote-server-not-found",
    "405": "not-allowed",
    "406": "not-acceptable",
    "407": "subscription-required",
    "409": "conflict",
    "500": "undefined-condition",
    "501": "feature-not-implemented",
    "503": "service-unavailable",
    "504": "remote-server-timeout"
}

sCodes = sorted(sCodesDesc.keys())
eCodes = sorted(eCodesDesc.keys())

isJID    = compile__(r"^.+?@[\w-]+?\.[\.\w-]+?$", 32)
isSource = lambda jid: bool(isJID.match(str(jid)))

# ── File Paths ─────────────────────────────────────────────────

static          = args.static   + "/%s"
dynamic         = args.dynamic  + "/%s"
# Absolut sekali di sini: expansions/lang baca ExpsDir global untuk scan
# locale. Kalau relatif, hasilnya tergantung cwd saat command jalan.
ExpsDir         = os.path.abspath(args.expansions)
FailDir         = dynamic % "crash"
PidFile         = dynamic % "sessions.db"
GenCrash        = dynamic % "dispatcher.crash"
GenConFile      = static  % "config.ini"
ConDispFile     = static  % "clients.ini"
ChatsFile       = dynamic % "chats.db"
ChatsFileBackup = dynamic % "chats.cp"
DatabaseFile    = dynamic % "users.db"

# ── Cache & Stats ──────────────────────────────────────────────

class AtomicNumber:
    """Thread-safe counter."""
    def __init__(self, start=0):
        self._val  = start
        self._lock = threading.Lock()

    def plus(self, n=1):
        with self._lock:
            self._val += n
            return self._val

    def value(self):
        with self._lock:
            return self._val

    def _str(self):
        return str(self.value())

    def __str__(self):
        return self._str()


VarCache = {
    "idle":   time.time(),
    "alive":  True,
    "errors": [],
    "action": "# %s %s &" % (os.path.basename(sys.executable), NxCore)
}

Info = {
    "cmd":    AtomicNumber(), "sess": time.time(),
    "msg":    AtomicNumber(), "alls": [],
    "cfw":    AtomicNumber(), "up":   1.0,
    "prs":    AtomicNumber(), "iq":   AtomicNumber(),
    "errors": AtomicNumber(),
    "omsg":   AtomicNumber(), "outiq": AtomicNumber()
}

# ── Global State ───────────────────────────────────────────────

expansions  = {}
Cmds        = {}
cPrefs      = ("!", "@", "#", ".", "*")
sCmds       = []
Chats       = {}
Guard       = {}
Clients     = {}       # jid_str -> NexusClient instance
NxLoop      = None     # satu shared asyncio loop (pola xmpp-platform)
_NX_RECONNECT_DELAY = {}  # disp -> detik backoff berikut, 5..300

# ── Reconnect guard (anti reconnect-storm) ───────────────────
# Bukti insiden 17.10 12:26-12:29: 23x connect dalam 3 menit,
# 22 di antaranya TANPA disconnect sebelumnya — timer yatim dari
# klien lama tetap menyalakan koneksi baru walau sesi sehat, lalu
# klien baru meng-nonaktifkan resource sama dan me-retrigger
# handler klien lama.  Tiga guard ditambah:
#   1. maksimal 1 timer reconnect per JID      -> _RECONN_TIMER
#   2. maksimal 1 percobaan connect per JID    -> _CONNECTING
#   3. token per klien, callback lama jadi basi -> _CLIENT_TOKEN
_RECONN_LOCK  = threading.Lock()
_RECONN_TIMER = {}    # disp -> threading.Timer (aktif, max 1 per JID)
_CONNECTING   = set() # disp yang sedang di dalam connect_client
_CLIENT_TOKEN = {}    # disp -> token klien yang kini dianggap sah
_CLIENT_SEQ   = [0]   # penomoran token (di bawah _RECONN_LOCK)

# ── Status hasil connect_client() — 3 state, bukan sukses/gagal ─
# Tuple-nya tetap 2 elemen (ok, status) supaya keempat pemanggil yang
# memakai `[0]` atau `ok, result = ...` tetap kompatibel tanpa diubah:
#   basic_control:172 (reconnect), config:155 (client add),
#   NexsusBot.py:2665 (reverseDisp), NexsusBot.py:2691 (connect_clients)
CC_CONNECTED  = "connected"   # sesi benar-benar aktif -> aman join
CC_CONNECTING = "connecting"  # connect lain sedang jalan -> BUKAN sukses
CC_FAILED     = "failed"      # percobaan selesai dan gagal
ChatsAttrs  = {}
Handlers    = {
    "01eh": [], "02eh": [], "03eh": [], "04eh": [],
    "05eh": [], "06eh": [], "07eh": [], "08eh": [],
    "09eh": [], "00si": [], "01si": [], "02si": [],
    "03si": [], "04si": []
}

Sequence    = threading.Semaphore()
NxSemaphore = threading.Semaphore()

# placeholders filled from config
GodName       = ""
DefNick       = "NexsusBot"
DefStatus     = "Nexus Online"
GenResource   = "Nexus"
Roster        = {"on": False}
Galist        = {}
InstancesDesc = {}
GenDisp       = ""
ConTls        = True
Mserve        = True
GetExc        = True
DefLANG       = "EN"
IncLimit      = 2000
PrivLimit     = 2000
ConfLimit     = 2000
ChatListLimit = 100
MaxMemory     = 0
Debug         = []

# ── Global AnsBase (dimuat dari static/insc.py saat startup) ──
# Nilai default (EN) — akan di-override oleh static/insc.py
AnsBase = (
    "This command is available only in the conferences.", # 0
    "This command requires arguments.",                  # 1
    "Invalid syntax.",                                    # 2
    "There is no '%s' in the chats-list.",               # 3
    "Done.",                                             # 4
    "Parameters should be shorter.",                     # 5
    "Such command doesn't exist.",                       # 6
    "I can't.",                                          # 7
    "There is no such conference in my list.",           # 8
    "Type is invalid.",                                  # 9
    "You need higher access.",                           # 10
    "You should look into private.",                     # 11
    "# %d. - %s",                                        # 12
    "command '%s' (%s)",                                 # 13
    "process '%s'",                                      # 14
    "While executing %s --> an error happened!",         # 15
    "Type --> 'excinfo %d' to show error (crashfile --> %s)", # 16
    "Type --> 'excinfo %d' or 'sh cat %s' to show error",    # 17
    "%s[...]\n\n** %d symbols limit! Type 'more' to show rest.", # 18
    "Command '%s' is unavailable now!",                  # 19
    "Error %s (%s) - conference: '%s'.",                 # 20
    "Error %s (%s), full exit from '%s'.",               # 21
    "Error %s (%s), I leaved '%s'.",                     # 22
    "The service without admin's affiliation is unavailable!", # 23
    "I disable all functions until I'll become an admin!", # 24
    "Obtaining rights...",                               # 25
    "sCode '%s' in %s (%s). Full leave!",                # 26
    "Type 'HELP' to know more (the last action - %s)",   # 27
    "Client '%s' fell!",                                 # 28
    "JID '%s' used in another client! (I have to disconnect it)", # 29
    "This is not a number."                              # 30
)

# Asyncio: setiap NexusClient memiliki loop asyncio sendiri di thread-nya

# ── Exceptions ─────────────────────────────────────────────────

class SelfExc(Exception):
    pass

class NexusExit(Exception):
    pass

class NodeProcessed(Exception):
    """Pengganti xmpp.NodeProcessed."""
    pass

# ── Utility Functions ──────────────────────────────────────────

def exc_info():
    exc, err, tb = sys.exc_info()
    if exc and err:
        exc = exc.__name__
        err = err.args[0] if err.args else None
    return (exc, err)


def exc_info_(fp=None):
    try:
        exc_info__(None, fp)
    except Exception:
        pass


def sleep(slp):
    time.sleep(slp)


def try_sleep(slp):
    try:
        sleep(slp)
    except KeyboardInterrupt:
        os._exit(0)
    except Exception:
        pass


def apply_safe(instance, args=(), kwargs={}):
    try:
        return instance(*args, **kwargs)
    except Exception:
        return None


def set_global(name, value):
    """
    Ubah variabel global di module NexsusBot ini secara langsung.

    Expansion dimuat via exec(code, g) dengan `g = {**globals()}` —
    sebuah SALINAN dict globals saat load. Di dalam expansion,
    `globals()[...] = value` hanya mengubah salinan tersebut, TIDAK
    mempengaruhi variabel asli di module ini (mis. MaxMemory, ConTls,
    DefStatus, dll yang dipakai di main loop / koneksi).

    Expansion yang perlu mengubah konfigurasi runtime harus memanggil
    set_global("NamaVariabel", nilai_baru) — fungsi ini berjalan di
    namespace asli NexsusBot, sehingga globals()[name] di sini adalah
    globals() module yang sebenarnya.
    """
    globals()[name] = value


def Exit(text, do_exit, slp, level=logging.INFO):
    # Level default INFO: Exit() juga dipakai untuk shutdown normal
    # (Ctrl+C, reload), bukan hanya kegagalan.  Pemanggil boleh naikkan
    # ke logging.ERROR kalau memang exit karena error.
    _Log(text, level)
    try_sleep(slp)
    if do_exit:
        os._exit(0)
    else:
        if not NxCore:
            sys.argv.pop(0)
        os.execl(sys.executable, sys.executable, *sys.argv)


def object_encode(obj):
    if isinstance(obj, str):
        return obj
    return str(obj)


strfTime = lambda fmt="%d.%m.%Y (%H:%M:%S)", local=True: time.strftime(
    fmt, time.localtime() if local else time.gmtime())

Yday     = lambda: time.gmtime().tm_yday
isNumber = lambda obj: str(obj).lstrip("-").isdigit()


def Time2Text(secs):
    """Localized duration text. See library/nxs_time.py.

    Historically this built English-only labels ("3 Minutes") with an English
    s-plural rule, so a Russian user saw "3 Minutes" inside an otherwise
    translated sentence. Kept as a module-level function because expansions
    import it directly.
    """
    from library.nxs_time import duration_text
    try:
        from library.nxs_l10n import LocalizationContext
        lang = LocalizationContext.get()
    except Exception:
        lang = "en"
    return duration_text(secs, lang)


def Size2Text(size):
    units = list("YZEPTGMK.")
    ext   = []
    while units:
        u = units.pop()
        if units:
            size, rest = divmod(size, 1024)
        else:
            rest = size
        if rest >= 1.0:
            suffix = u if u != "." else ""
            ext.insert(0, "%d%sB" % (int(rest), suffix))
        if not (units and size):
            return " ".join(ext)
    return "0B"


enumerated_list = lambda ls: "\n".join(
    "%d) %s" % (i, line) for i, line in enumerate(ls, 1))

# ── File I/O ───────────────────────────────────────────────────

def initialize_file(filename, data="{}"):
    if os.path.isfile(filename):
        return True
    try:
        folder = os.path.dirname(filename)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, 0o755)
        cat_file(filename, data)
    except Exception:
        return False
    return True


def del_file(filename):
    os.remove(filename)


def get_file(filename):
    with open(filename, "r", encoding="utf-8") as fp:
        return fp.read()


def cat_file(filename, data, otype="w"):
    with Sequence:
        with open(filename, otype, encoding="utf-8") as fp:
            fp.write(data)


chat_file = lambda chat, name: dynamic % ("%s/%s" % (chat, name))

# ── Database ───────────────────────────────────────────────────

class Database:
    """Simple SQLite context manager."""

    def __init__(self, dbfile, semaphore=None):
        self.dbfile    = dbfile
        self.semaphore = semaphore
        self._conn     = None
        self._cur      = None

    def __enter__(self):
        if self.semaphore:
            self.semaphore.acquire()
        self._conn = sqlite3.connect(self.dbfile)
        self._cur  = self._conn.cursor()
        return self

    def __exit__(self, *args):
        if self._conn:
            self._conn.close()
        if self.semaphore:
            self.semaphore.release()

    def __call__(self, query, args=()):
        self._cur.execute(query, args)

    def commit(self):
        self._conn.commit()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchone(self):
        return self._cur.fetchone()


def runDatabaseQuery(query, args=(), set=False, many=True):
    semph = None
    if threading.current_thread().name != "MainThread":
        semph = NxSemaphore
    with Database(DatabaseFile, semph) as db:
        db(query, args)
        if set:
            db.commit()
            return None
        elif many:
            return db.fetchall()
        else:
            return db.fetchone()

# ── Crash / Error Logging ──────────────────────────────────────

def crashLog(inst):
    crash_dir = os.path.dirname(GenCrash)
    if crash_dir and not os.path.exists(crash_dir):
        os.makedirs(crash_dir, exist_ok=True)
    with open(GenCrash, "a", encoding="utf-8") as fp:
        fp.write("\n\n--- CRASH [%s] ---\n%s\n" % (inst, traceback.format_exc()))


def collectDFail():
    PrintErr("Critical failure!")
    crashLog("dispatcher")


def collectExc(inst, command=None):
    error  = traceback.format_exc()
    VarCache["errors"].append(error)
    name   = getattr(inst, "__name__", str(inst))
    number = len(VarCache["errors"])
    msg    = "Error in '%s' (command=%s)\n%s" % (name, command, error)
    PrintErr(msg)
    logger.error(msg)
    crashLog(name)

# ── Threading Helpers ──────────────────────────────────────────

_aCounter = AtomicNumber()


def composeThr(handler, name, lst=(), command=None):
    def runner():
        try:
            handler(*lst)
        except SystemExit:
            pass
        except KeyboardInterrupt:
            pass
        except SelfExc:
            pass
        except Exception:
            collectExc(handler, command)
    t = threading.Thread(target=runner, name=name, daemon=True)
    return t


def composeTimer(slp, handler, name=None, lst=()):
    if not name:
        name = "NxTimer-%s" % _aCounter._str()
    def runner():
        time.sleep(slp)
        try:
            handler(*lst)
        except Exception:
            collectExc(handler)
    t = threading.Thread(target=runner, name=name, daemon=True)
    return t


# ── Reconnect guard helpers ──────────────────────────────────
# Ditaruh setelah composeTimer sengaja: composeTimer TIDAK dipakai
# lagi untuk reconnect (5 call site lain tetap pakai, tak diubah).

def _new_client_token():
    """Token unik per NexusClient — untuk membuang callback klien lama."""
    with _RECONN_LOCK:
        _CLIENT_SEQ[0] += 1
        return _CLIENT_SEQ[0]


def _reconn_log(fmt, *args):
    """Log diagnostik jalur reconnect (level DEBUG -> hanya ke nexsus.log,
    tidak memenuhi console karena FILE_LEVEL=DEBUG).

    Aturan keras: kegagalan MENULIS log tidak boleh menggagalkan reconnect.
    Kalau _Log melempar exception di sini dan dibiarkan, satu bug logging
    berarti bot tidak pernah reconnect lagi. Semua ditelan di sini.
    """
    try:
        _Log(fmt % args if args else fmt, logging.DEBUG)
    except Exception:
        pass


def _cancel_reconn(disp):
    """Batalkan timer reconnect aktif milik JID/disp (bila ada)."""
    with _RECONN_LOCK:
        timer = _RECONN_TIMER.pop(disp, None)
    if timer is not None:
        try:
            timer.cancel()
        except Exception:
            pass
        _reconn_log("[reconn] timer cancelled jid=%s (new connection already succeeded)",
                    disp)


def _schedule_reconn(disp, delay, token):
    """Jadwalkan reconnect dengan 3 syarat, supaya storm mustahil terjadi:
       - token masih sah (klien pemanggil belum digantikan),
       - belum ada percobaan connect berjalan,
       - tidak ada timer aktif lain untuk JID sama (yang lama dibatalkan).
    """
    with _RECONN_LOCK:
        if _CLIENT_TOKEN.get(disp) != token:
            # Bahan bakar storm sebelumnya: klien lama masih bisa bikin
            # timer baru. Sekarang dibuang, dan dicatat supaya peristiwa
            # seperti 18.10 00:02:51 bisa ditafsirkan dari log.
            _reconn_log("[reconn] timer NOT scheduled jid=%s: "
                        "stale token (timer=%s, active=%s)",
                        disp, token, _CLIENT_TOKEN.get(disp))
            return                      # callback klien lama -> buang
        old = _RECONN_TIMER.get(disp)
        if old is not None:
            try:
                old.cancel()            # hanya 1 timer per JID
            except Exception:
                pass
            _RECONN_TIMER.pop(disp, None)
            _reconn_log("[reconn] previous timer cancelled jid=%s", disp)

        def _fire():
            t0 = time.time()
            with _RECONN_LOCK:
                _RECONN_TIMER.pop(disp, None)
                stale = (_CLIENT_TOKEN.get(disp) != token) or (disp in _CONNECTING)
            if stale:
                _reconn_log("[reconn] timer fired jid=%s -> ABORT "
                            "(active token=%s timer token=%s in-flight=%s, "
                            "%.3fs after creation)",
                            disp, _CLIENT_TOKEN.get(disp), token,
                            disp in _CONNECTING, time.time() - t0)
                return                  # sesi sudah berganti / sedang connect
            cur = Clients.get(disp)
            if cur is not None and cur.isConnected():
                _reconn_log("[reconn] timer fired jid=%s -> ABORT "
                            "(already connected, %.3fs after creation)",
                            disp, time.time() - t0)
                return                  # sudah terhubung -> jangan connect lagi
            # Titik krusial: jarak antara "timer fire" dan "connecting..."
            # di _connect_client_body menunjukkan di mana jeda 39 detik
            # pada peristiwa 18.10 00:02 itu terjadi.
            _reconn_log("[reconn] timer fired jid=%s -> reverseDisp "
                        "(%.3fs after creation)", disp, time.time() - t0)
            reverseDisp(disp)
            _reconn_log("[reconn] reverseDisp finished jid=%s "
                        "(%.3fs after timer fired)", disp, time.time() - t0)

        timer = threading.Timer(delay, _fire)
        timer.daemon = True
        _RECONN_TIMER[disp] = timer
        timer.start()
        # delay riil harus sama dengan delay yang diminta; kalau beda,
        # berarti timer thread-nya tertahan (kandidat penyebab jeda aneh).
        _reconn_log("[reconn] timer created jid=%s delay=%ss token=%s",
                    disp, delay, token)


def sThread(name, inst, lst=(), command=None):
    composeThr(inst, name, lst, command).start()


def call_sfunctions(ls, lst=()):
    for inst in Handlers[ls]:
        try:
            inst(*lst)
        except Exception:
            collectExc(inst)


def call_efunctions(ls, lst=()):
    for inst in Handlers[ls]:
        sThread(ls, inst, lst)

# ── Asyncio Bridge ─────────────────────────────────────────────
# slixmpp berjalan di asyncio event loop di thread terpisah.
# Helper ini memungkinkan pemanggilan coroutine dari thread biasa.

def _get_client_loop(disp=None):
    """Shared loop (pola xmpp-platform). Argumen disp dipertahankan
    supaya call site lama tidak perlu diubah."""
    loop = globals().get("NxLoop")
    if loop is not None and loop.is_running():
        return loop
    return None


def run_coro(coro, disp=None):
    """Jalankan coroutine dari thread manapun secara blocking."""
    loop = _get_client_loop(disp)
    if loop is None:
        return None
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return future.result(timeout=30)
    except Exception:
        exc_info_()
        return None


def schedule_coro(coro, disp=None):
    """Jadwalkan coroutine tanpa menunggu hasilnya."""
    import inspect
    # Kalau bukan coroutine (mis. disconnect() return None di slixmpp tertentu)
    # — buang saja, tidak perlu di-schedule
    if coro is None or not inspect.isawaitable(coro):
        try:
            coro.close()
        except Exception:
            pass
        return
    loop = _get_client_loop(disp)
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(coro, loop)


def client_loop(client):
    """Loop untuk menjalankan IQ/coroutine milik client.

    Sejak rombak B (shared NxLoop), client tidak lagi menyimpan _loop
    sendiri — pakai shared loop. Fallback ke atribut lama kalau ada,
    supaya ekspansi yang belum diupdate tetap jalan.
    """
    loop = _get_client_loop()
    if loop is not None:
        return loop
    return getattr(client, "_loop", None)

# ── Config Loader ──────────────────────────────────────────────

def client_config(config, section):
    serv = config.get(section, "serv").lower()
    port = config.get(section, "port")
    if not port.isdigit():
        port = "5222"
    port = int(port)
    user = config.get(section, "user").lower()
    host = config.get(section, "host").lower()
    password = config.get(section, "pass")
    jid  = "%s@%s" % (user, host)
    return (jid, (serv, port, host, user, password))


GenCon  = None   # configparser.ConfigParser untuk static/config.ini
ConDisp = None   # configparser.ConfigParser untuk static/clients.ini


def _apply_nxsus_env_overrides(config):
    """Muat .env tanpa menimpa environment; override config secara selektif."""
    if load_dotenv is not None:
        load_dotenv(
            dotenv_path=os.path.join(NxRoot or os.getcwd(), ".env"),
            override=False,
        )

    mapping = {
        "NXSUS_XMPP_SERVER": ("CLIENT", "serv"),
        "NXSUS_XMPP_PORT": ("CLIENT", "port"),
        "NXSUS_XMPP_USER": ("CLIENT", "user"),
        "NXSUS_XMPP_HOST": ("CLIENT", "host"),
        "NXSUS_XMPP_PASSWORD": ("CLIENT", "pass"),
        "NXSUS_TLS": ("STATES", "tls"),
        "NXSUS_MSERVE": ("STATES", "mserve"),
        "NXSUS_GETEXC": ("STATES", "getexc"),
        "NXSUS_LANG": ("STATES", "lang"),
        "NXSUS_ADMIN_JID": ("CONFIG", "admin"),
        "NXSUS_NICK": ("CONFIG", "nick"),
        "NXSUS_STATUS": ("CONFIG", "status"),
        "NXSUS_XMPP_RESOURCE": ("CONFIG", "resource"),
        "NXSUS_LOG_LEVEL": ("LOGGING", "level"),
        "NXSUS_LOG_FILE_LEVEL": ("LOGGING", "file_level"),
        "NXSUS_LOG_FILE": ("LOGGING", "file"),
        "NXSUS_LOG_CONSOLE": ("LOGGING", "console"),
        "NXSUS_LOG_MAX_BYTES": ("LOGGING", "max_bytes"),
        "NXSUS_LOG_BACKUP_COUNT": ("LOGGING", "backup_count"),
        "NXSUS_LIMIT_MEMORY_MB": ("LIMITS", "memory"),
        "NXSUS_LIMIT_INCOMING": ("LIMITS", "incoming"),
        "NXSUS_LIMIT_CHAT": ("LIMITS", "chat"),
        "NXSUS_LIMIT_PRIVATE": ("LIMITS", "private"),
        "NXSUS_LIMIT_CHAT_LIST": ("LIMITS", "chat_list_length"),
    }

    for env_key, (section, option) in mapping.items():
        value = os.environ.get(env_key)
        # Nilai kosong pada template tidak boleh menghapus konfigurasi lama.
        if value is None or not value.strip():
            continue
        if not config.has_section(section):
            config.add_section(section)
        # Escape interpolasi ConfigParser untuk semua nilai environment.
        value = value.replace("%", "%%")
        config.set(section, option, value)


def load_config():
    global GodName, DefNick, DefStatus, GenResource
    global _lang_warn
    global ConTls, Mserve, GetExc, DefLANG
    global IncLimit, PrivLimit, ConfLimit, ChatListLimit, MaxMemory
    global Debug, GenDisp, InstancesDesc, Galist
    global GenCon, ConDisp

    try:
        GenCon = configparser.ConfigParser()
        GenCon.read(GenConFile)
        _apply_nxsus_env_overrides(GenCon)
        GenDisp, Instance  = client_config(GenCon, "CLIENT")
        InstancesDesc      = {GenDisp: Instance}
        ConTls             = GenCon.getboolean("STATES", "TLS",    fallback=True)
        Mserve             = GenCon.getboolean("STATES", "MSERVE", fallback=True)
        GetExc             = GenCon.getboolean("STATES", "GETEXC", fallback=True)
        raw_lang = GenCon.get("STATES", "LANG", fallback="EN")
        if os.environ.get("NXSUS_LANG", "").strip():
            DefLANG = raw_lang.strip()
        else:
            DefLANG = raw_lang.upper()[:2]
        # Normalisasi + validasi kode bahasa.  Nilai lama di-parse dengan
        # .upper()[:2], jadi "Indonesian" jadi "IN" - bukan kode bahasa.
        # normalize() memetakan alias ke kode yang benar; kalau hasilnya
        # tidak dikenal, tetap jalan dengan kode itu dan beri warning.
        _lang_warn = None
        if nxs_lang is not None:
            _lang_warn = nxs_lang.warn_if_unknown(
                GenCon.get("STATES", "LANG", fallback="EN"))
            DefLANG = nxs_lang.normalize(DefLANG)
        else:
            DefLANG = DefLANG.lower()
        GodName            = GenCon.get("CONFIG", "ADMIN",    fallback="admin@localhost").lower()
        DefNick            = GenCon.get("CONFIG", "NICK",     fallback="NexsusBot").split()[0]
        DefStatus          = GenCon.get("CONFIG", "STATUS",   fallback="Nexus Online")
        GenResource        = GenCon.get("CONFIG", "RESOURCE", fallback="Nexus")
        IncLimit           = int(GenCon.get("LIMITS", "INCOMING",         fallback="2000"))
        PrivLimit          = int(GenCon.get("LIMITS", "PRIVATE",          fallback="2000"))
        ConfLimit          = int(GenCon.get("LIMITS", "CHAT",             fallback="2000"))
        ChatListLimit      = int(GenCon.get("LIMITS", "CHAT_LIST_LENGTH", fallback="100"))
        MaxMemory          = int(GenCon.get("LIMITS", "MEMORY",           fallback="0")) * 1024

        # [LOGGING] opsional — section hilang → default LogManager tetap berlaku.
        logMgr.configure(GenCon)

        try:
            Debug = eval(GenCon.get("CONFIG", "DEBUG"))
        except (configparser.NoOptionError, Exception):
            Debug = []

        ConDisp = configparser.ConfigParser()
        if os.path.isfile(ConDispFile):
            ConDisp.read(ConDispFile)
            for Block in ConDisp.sections():
                Disp, Inst = client_config(ConDisp, Block)
                InstancesDesc[Disp] = Inst

        Galist = {GodName: 8}
        return True

    except Exception:
        exc_info_()
        Exit(
            "One of the configuration files is missing or corrupted!\n"
            "  Create static/config.ini with [CLIENT], [STATES], [CONFIG], [LIMITS] sections.",
            True, 2, level=logging.ERROR)

# ── NexusClient — slixmpp wrapper ─────────────────────────────

class NexusClient(ClientXMPP):
    """
    Wrapper ClientXMPP (slixmpp) yang mengadaptasi antarmuka
    lama berbasis callback threading ke asyncio slixmpp.
    """

    def __init__(self, jid_str, password, server, port, resource):
        full_jid = "%s/%s" % (jid_str, resource)
        super().__init__(full_jid, password)

        self._nx_jid      = jid_str
        self._nx_server   = server
        self._nx_port     = port
        self._connected   = False
        self._roster_obj  = None
        self.RespExp      = {}          # IQ response callbacks

        # Pola xmpp-platform: stream harus terbukti hidup. Tanpa ini,
        # socket idle di-reap server/NAT dalam hitungan menit dan bot
        # mengira masih connect (silent disconnect).
        self.enable_starttls = True
        self.enable_direct_tls = False
        self.enable_plaintext = False
        self.whitespace_keepalive = True
        self.whitespace_keepalive_interval = 60

        # Pola xmpp-platform: tolak stream yang menawarkan SASL tanpa
        # STARTTLS. Tanpa ini, slixmpp lanjut ke SASL di atas plaintext,
        # lalu mati dengan "No appropriate login method" yang menyesatkan.
        # (mech PLAIN butuh encrypted=True; encrypted butuh starttls/SSL.)

        # Register slixmpp plugins
        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0045")  # MUC
        self.register_plugin("xep_0092")  # Version
        self.register_plugin("xep_0012")  # Last Activity (uptime/idle)
        self.register_plugin("xep_0202")  # Entity Time
        self.register_plugin("xep_0054")  # vCard-temp
        self.register_plugin("xep_0115")  # Entity Capabilities (XEP-0115)
        self.register_plugin("xep_0199")  # Ping
        self.register_plugin("xep_0203")  # Delayed Delivery
        self.register_plugin("xep_0085")  # Chat State Notifications
        self.register_plugin("xep_0184")  # Message Receipts

        # Event handlers
        self.add_event_handler("session_start",        self._on_session_start)
        self.add_event_handler("disconnected",         self._on_disconnected)
        self.add_event_handler("message",              self._on_message)
        self.add_event_handler("presence",             self._on_presence)
        self.add_event_handler("groupchat_message",    self._on_groupchat_message)
        self.add_event_handler("groupchat_presence",   self._on_groupchat_presence)
        self.add_event_handler("changed_subscription", self._on_subscription)

        # Server dengan cert chain tidak lengkap/self-signed (mis. xmpp.jp)
        # akan trigger "ssl_invalid_chain" — tanpa handler ini slixmpp
        # langsung disconnect(). Kita terima koneksi tetap lanjut
        # (CERT TIDAK divalidasi penuh — risiko MITM, tapi banyak server
        # publik punya chain tidak lengkap dan tetap aman secara praktik).
        self.add_event_handler("ssl_invalid_chain", self._on_ssl_invalid_chain)

    async def _on_ssl_invalid_chain(self, event):
        PrintWarn('"%s" cert trust chain invalid — lanjut tanpa verifikasi penuh.' % self._nx_jid)
        # Tidak memanggil disconnect() — biarkan slixmpp lanjut handshake

    async def _handle_stream_features(self, features):
        # Pola xmpp-platform: tolak stream yang menawarkan SASL tanpa
        # STARTTLS. Tanpa ini, slixmpp lanjut ke SASL di atas plaintext,
        # lalu mati dengan "No appropriate login method" yang menyesatkan.
        offered = features["features"]
        if (
            "mechanisms" in offered
            and "starttls" not in offered
            and "starttls" not in self.features
        ):
            self.disconnect(wait=0, reason="STARTTLS required before authentication")
            return True
        return await super()._handle_stream_features(features)


    # ── slixmpp event handlers ─────────────────────────────────

    async def _on_session_start(self, event):
        self._connected = True
        self._roster_obj = self.client_roster
        await self.get_roster()
        self.send_presence(pshow=sList[0], pstatus=DefStatus)
        # Set info yang muncul saat client lain cek IQ version
        try:
            import platform as _plt
            _os   = _plt.system()              # Windows / Linux
            _rv   = _plt.release()             # 10 / 4.4.0-22621-Microsoft
            _mach = _plt.machine()             # x86_64 / aarch64
            _pyim = _plt.python_implementation() # CPython
            _pyv  = _plt.python_version()      # 3.13.0
            _os_str = "%s %s [%s] / %s [%s]" % (_os, _rv, _mach, _pyim, _pyv)

            # slixmpp 1.15.0: override via plugin config
            xep92 = self.plugin["xep_0092"]

            # Cara 1: set_plugin_config (slixmpp 1.15+)
            if hasattr(xep92, "name"):
                xep92.name    = ProdName
                xep92.version = ProdVer
                xep92.os      = _os_str

            # Cara 2: update plugin_config dict
            cfg = getattr(xep92, "config", None) or {}
            cfg.update({
                "software_name": ProdName,
                "version":       ProdVer,
                "os":            _os_str,
            })
            if hasattr(xep92, "config"):
                xep92.config = cfg

            # Cara 3: langsung ke atribut yang dipakai saat build response
            for attr, val in (
                ("software_name", ProdName),
                ("version",       ProdVer),
                ("os",            _os_str),
            ):
                if hasattr(xep92, attr):
                    setattr(xep92, attr, val)

        except Exception:
            pass
        PrintOK('"%s" session started!' % self._nx_jid)
        for conf in list(Chats.values()):
            if conf.disp == self._nx_jid:
                conf.join()

    async def _on_disconnected(self, event):
        self._connected = False
        PrintWarn('"%s" disconnected!' % self._nx_jid)
        if VarCache["alive"]:
            token   = getattr(self, "_nx_token", None)
            current = _CLIENT_TOKEN.get(self._nx_jid)
            # LOG RECONNECT: bedakan "klien AKTIF benar-benar putus"
            # dari "klien LAMA di-teardown setelah klien baru sukses".
            # Peristiwa 18.10 00:02:51 (disconnected 0 dtk setelah
            # authenticated) tidak mungkin ditafsirkan tanpa baris ini.
            _reconn_log("[reconn] disconnected jid=%s this_client_token=%s "
                        "active_token=%s", self._nx_jid, token, current)
            # Callback dari klien yang sudah digantikan tidak boleh
            # menjadwalkan reconnect tambahan — inilah bahan bakar
            # reconnect-storm (klien lama di-kick klien baru, lalu
            # handlernya menyalakan koneksi berikutnya, selamanya).
            if token is None or current != token:
                _reconn_log("[reconn] ignored: stale client callback "
                            "jid=%s -> NO reconnect scheduled",
                            self._nx_jid)
                return
            delay = _NX_RECONNECT_DELAY.get(self._nx_jid, 5)
            _reconn_log("[reconn] scheduling reconnect jid=%s delay=%ss "
                        "next_backoff=%ss",
                        self._nx_jid, delay, min(delay * 2, 300))
            # Maksimal 1 timer per JID; timer lama dibatalkan di dalam.
            _schedule_reconn(self._nx_jid, delay, token)
            # Backoff tetap dipertahankan: 5 -> 10 -> ... -> 300.
            _NX_RECONNECT_DELAY[self._nx_jid] = min(delay * 2, 300)
        # Loop milik bersama (NxLoop) — jangan stop di sini.

    async def _on_subscription(self, presence):
        """Handle subscribe/unsubscribe."""
        ptype  = presence["type"]
        sender = str(presence["from"].bare)
        if ptype == "subscribe":
            if enough_access(sender, sender, 7):
                self.send_presence(pto=sender, ptype="subscribed")
                self.send_presence(pto=sender, ptype="subscribe")
            elif Roster["on"]:
                self.send_presence(pto=sender, ptype="subscribed")
                self.send_presence(pto=sender, ptype="subscribe")
            else:
                self.send_presence(pto=sender, ptype="unsubscribed")

    async def _on_presence(self, presence):
        """Presence 1-to-1 (bukan MUC)."""
        pass

    async def _on_groupchat_presence(self, presence):
        """MUC presence."""
        Info["prs"].plus()
        sThread("presence", _handle_presence, (self._nx_jid, presence))

    async def _on_message(self, msg):
        """Pesan 1-to-1."""
        if msg["type"] in ("chat", "normal", "error"):
            Info["msg"].plus()
            sThread("message", _handle_message, (self._nx_jid, msg))

    async def _on_groupchat_message(self, msg):
        """Pesan MUC."""
        Info["msg"].plus()
        sThread("groupchat_msg", _handle_message, (self._nx_jid, msg))

    # ── Public API ─────────────────────────────────────────────

    def isConnected(self):
        return self._connected

    def nx_disconnect(self):
        """Disconnect via shared loop."""
        try:
            loop = globals().get("NxLoop")
            if not loop or not loop.is_running():
                return
            import inspect
            result = self.disconnect()
            if inspect.isawaitable(result):
                asyncio.run_coroutine_threadsafe(result, loop)
            # Jika bukan coroutine, disconnect sudah terjadi sinkron
        except Exception:
            pass

    def _schedule(self, coro):
        """Schedule coroutine ke shared loop."""
        loop = globals().get("NxLoop")
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
        else:
            try:
                coro.close()
            except Exception:
                pass

    def nx_send(self, stanza_or_msg):
        """Thread-safe send."""
        if isinstance(stanza_or_msg, str):
            self._schedule(self._async_send_raw(stanza_or_msg))
        else:
            self._schedule(self._async_send(stanza_or_msg))

    async def _async_send(self, stanza):
        try:
            stanza.send()
        except Exception:
            exc_info_()

    async def _async_send_raw(self, raw):
        try:
            self.send_raw(raw)
        except Exception:
            exc_info_()

    def nx_send_message(self, to, body, mtype="chat"):
        self._schedule(self._send_message_coro(to, body, mtype))

    async def _send_message_coro(self, to, body, mtype):
        try:
            msg = self.make_message(mto=to, mbody=body, mtype=mtype)
            msg.send()
        except Exception:
            exc_info_()

    def nx_send_presence(self, **kwargs):
        self._schedule(self._send_presence_coro(**kwargs))

    async def _send_presence_coro(self, **kwargs):
        try:
            self.send_presence(**kwargs)
        except Exception:
            exc_info_()

    def nx_join_muc(self, room, nick, password=None):
        self._schedule(self._join_muc_coro(room, nick, password))

    async def _join_muc_coro(self, room, nick, password=None):
        try:
            muc = self.plugin["xep_0045"]
            # join_muc_wait dengan timeout lebih panjang + suppress TimeoutError
            # TimeoutError bukan fatal — bot tetap join, server hanya lambat respond
            try:
                if password:
                    await muc.join_muc_wait(room, nick, password=password, timeout=30)
                else:
                    await muc.join_muc_wait(room, nick, timeout=30)
            except asyncio.TimeoutError:
                pass  # Bot tetap join, presence sudah dikirim
            except Exception:
                # Fallback: fire-and-forget
                if password:
                    muc.join_muc(room, nick, password=password)
                else:
                    muc.join_muc(room, nick)
        except Exception:
            exc_info_()

    def nx_leave_muc(self, room, nick, status=None):
        self._schedule(self._leave_muc_coro(room, nick, status))

    async def _leave_muc_coro(self, room, nick, status=None):
        try:
            muc = self.plugin["xep_0045"]
            muc.leave_muc(room, nick, msg=status or "")
        except Exception:
            exc_info_()

    def nx_set_affiliation(self, room, jid, affiliation, reason=""):
        self._schedule(self._set_affiliation_coro(room, jid, affiliation, reason))

    async def _set_affiliation_coro(self, room, jid, affiliation, reason=""):
        try:
            muc = self.plugin["xep_0045"]
            await muc.set_affiliation(room, jid=jid,
                                       affiliation=affiliation, reason=reason)
        except (IqError, IqTimeout) as e:
            PrintErr("affiliation error: %s" % e)

    def nx_set_role(self, room, nick, role, reason=""):
        self._schedule(self._set_role_coro(room, nick, role, reason))

    async def _set_role_coro(self, room, nick, role, reason=""):
        try:
            muc = self.plugin["xep_0045"]
            await muc.set_role(room, nick, role, reason=reason)
        except (IqError, IqTimeout) as e:
            PrintErr("role error: %s" % e)

    def nx_send_subject(self, room, subject):
        self._schedule(self._send_subject_coro(room, subject))

    async def _send_subject_coro(self, room, subject):
        try:
            msg = self.make_message(mto=room, mtype="groupchat")
            msg["subject"] = subject
            msg.send()
        except Exception:
            exc_info_()

# ── XMPP Helper Functions ──────────────────────────────────────

def get_disp(disp):
    """Kembalikan jid string dari NexusClient atau string."""
    if isinstance(disp, NexusClient):
        return disp._nx_jid
    return disp


def online(disp):
    disp = get_disp(disp)
    if disp in Clients:
        return Clients[disp].isConnected()
    return False


def Sender(disp, payload):
    """
    Kirim pesan/stanza melalui client.
    payload bisa berupa dict: {"to": ..., "body": ..., "type": "chat"}
    """
    try:
        key = get_disp(disp)
        if key not in Clients:
            raise SelfExc("client '%s' not found" % key)
        client = Clients[key]
        if isinstance(payload, dict):
            to    = payload.get("to", "")
            body  = payload.get("body", "")
            mtype = payload.get("type", "chat")
            if body:
                client.nx_send_message(to, body, mtype)
            ptype = payload.get("ptype")
            if ptype is not None:
                client.nx_send_presence(pto=to, ptype=ptype,
                                         pshow=payload.get("pshow"),
                                         pstatus=payload.get("pstatus"))
        else:
            client.nx_send(payload)
    except IOError:
        pass
    except SelfExc as e:
        PrintErr(str(e))
    except Exception:
        exc_info_()


def delivery(body):
    """Kirim pesan langsung ke GodName."""
    try:
        Disp = GenDisp
        body = object_encode(body)
        if not online(Disp):
            for disp in Clients:
                if disp != GenDisp and online(disp):
                    Disp = disp
                    break
            if not online(Disp):
                raise SelfExc("all clients disconnected")
        Info["omsg"].plus()
        Clients[Disp].nx_send_message(GodName, body, sBase[0])
    except (IOError, SelfExc) as e:
        PrintWarn("[DELIVERY FAIL] %s\n  %s" % (e, body))
    except Exception:
        exc_info_()


def get_nick(chat):
    return getattr(Chats.get(chat), sBase[12], DefNick)


def get_source(source, nick):
    if source in Chats:
        return getattr(Chats[source].get_user(nick), "source", None)
    return source


def _get_user_lang(chat, nick):
    """
    Bahasa yang dipilih eksplisit lewat command `lang`, atau None.

    None berarti user belum memilih - pemanggil lalu memakai tag <lang/>
    dari presence, lalu DefLANG.  Modul userlang boleh None kalau import
    gagal; itu hanya berarti belum ada yang bisa memilih bahasa, bukan error.
    """
    if nxs_userlang is None:
        return None
    return nxs_userlang.get_user_lang(chat, nick)


def _presence_lang(presence, default=None):
    """
    Ambil tag <lang/> dari presence stanza (XEP-0115) dan normalkan.

    Karena itu: client seperti Conversations/Monocle mengirim bahasa client
    mereka di setiap presence available.  Ini hanya deteksi otomatis -
    pilihan eksplisit lewat command `lang` menang (lihat _set_reply_lang).
    """
    default = default if default is not None else DefLANG
    try:
        el = presence.xml.find(".//{http://jabber.org/protocol/caps}lang")
        if el is None:
            el = presence.xml.find(".//lang")
        if el is not None and el.text:
            return nxs_lang.normalize(el.text, default=default)
    except Exception:
        exc_info_()
    return nxs_lang.normalize(default, default="en")


def getLang(source):
    """
    Dari BlackSmith: ambil bahasa user dari Chats (untuk multi-lang expansion).
    source bisa berupa tuple (source, conf, nick) atau string conf.

    Urutan prioritas:
      1. Pilihan eksplisit dari command `lang` (tabel userlang.db)
      2. Tag <lang/> dari presence (client language)
      3. DefLANG dari config
    """
    if isinstance(source, (tuple, list)) and len(source) > 2:
        chat = Chats.get(source[1])
        if chat:
            user = chat.get_user(source[2])
            if user:
                # Pilihan eksplisit menang atas presence.
                try:
                    chosen = _get_user_lang(source[1], source[2])
                except Exception:
                    exc_info_()
                    chosen = None
                if chosen:
                    return chosen
                # sUser.lang diisi dari presence (lihat _presence_lang).
                lang = getattr(user, "lang", None)
                if lang:
                    return nxs_lang.normalize(lang, default=DefLANG.lower())
                return DefLANG.lower()
    return DefLANG.lower()


def get_full_source(conf, nick):
    """
    JID lengkap (dengan resource) milik user di room — untuk target IQ
    (vcard-temp, urn:xmpp:time, jabber:iq:version, ping). Fallback ke
    bare JID (get_source) jika full_jid tidak diketahui.
    """
    if conf in Chats:
        user = Chats[conf].get_user(nick)
        if user:
            return getattr(user, "full_jid", None) or getattr(user, "source", None)
    return None


def get_access(source, nick):
    if source in Chats:
        user = Chats[source].get_user(nick)
        if user is None:
            return 0
        # JID diketahui — cek Galist/alist (prioritas, bisa berubah runtime)
        if user.source:
            explicit = Galist.get(user.source)
            if explicit is None:
                explicit = Chats[source].alist.get(user.source)
            if explicit is not None:
                return explicit
        # Tidak ada JID atau tidak ada di Galist — pakai access dari role/aff
        return user.access
    # Private chat — source adalah JID langsung
    return Galist.get(source, 2)


enough_access = lambda conf, nick, access=0: (access <= get_access(conf, nick))


def Message(inst, body, disp=None):
    """Kirim pesan ke room atau JID."""
    body = object_encode(body)
    _Log("reply ke %s: %s" % (inst, body[:120].replace("\n", " | ")), logging.INFO)
    if inst in Chats:
        mtype = sBase[1]  # groupchat
        if not disp:
            disp = Chats[inst].disp
        if len(body) > ConfLimit:
            Chats[inst].more = body[ConfLimit:].strip()
            body = "%s[...] (%d limit)" % (body[:ConfLimit].strip(), ConfLimit)
    else:
        mtype = sBase[0]  # chat
        if not disp:
            chat = inst.split("/")[0].lower()
            disp = Chats[chat].disp if chat in Chats else GenDisp
        if len(body) > PrivLimit:
            chunks = [body[i:i+PrivLimit] for i in range(0, len(body), PrivLimit)]
            total  = len(chunks)
            for n, chunk in enumerate(chunks[:-1], 1):
                Info["omsg"].plus()
                Sender(disp, {"to": inst, "body": "[%d/%d] %s[...]" % (n, total, chunk.strip()), "type": mtype})
                sleep(2)
            body = "[%d/%d] %s" % (total, total, chunks[-1].strip())
    Info["omsg"].plus()
    Sender(disp, {"to": inst, "body": body.strip(), "type": mtype})


def Answer(body, stype, source, disp=None):
    if stype == sBase[0]:
        instance = source[0]
        Message(instance, object_encode(body), disp)
    else:
        body     = "%s: %s" % (source[2], object_encode(body))
        instance = source[1]
        Message(instance, body, disp)


def IdleClient():
    cls = {disp: 0 for disp in Clients if online(disp)}
    for conf in Chats.values():
        if conf.disp in cls:
            cls[conf.disp] += 1
    if cls:
        idle = min(cls.values())
        for disp, n in cls.items():
            if n == idle:
                return disp
    return GenDisp


def checkFlood(disp):
    key = get_disp(disp)
    if key not in Guard:
        Guard[key] = []
    Guard[key].append(time.time())
    if len(Guard[key]) > 3:
        if Guard[key][-1] - Guard[key][0] < 9:
            Guard[key] = [Guard[key].pop()]
            raise NodeProcessed()
        else:
            Guard[key].pop(0)

# ── User & Chat Classes ────────────────────────────────────────

class sUser:
    """Merepresentasikan peserta MUC."""

    def __init__(self, nick, role, source, access=None, caps=None, lang=None, full_jid=""):
        self.nick              = nick
        self.source            = source       # bare JID — untuk access list (Galist)
        self.full_jid          = full_jid or source  # JID+resource — untuk target IQ
        self.role              = role
        self.ishere            = True
        self.caps              = caps or {}
        self.lang              = lang or DefLANG.lower()
        self.date              = (time.time(), Yday(), strfTime(local=False))
        self.last_message_time = time.time()
        self.access            = access
        if access is None:
            self.calc_acc()

    def aroles(self, role):
        if self.role != role:
            self.role = role
            return True
        return False

    def setNick(self, newNick):
        self.nick = newNick
        return self

    def setJid(self, newJid):
        self.jid = newJid
        return self

    def isSuspicious(self):
        return time.time() - self.date[0]

    def updateLastMessageTime(self):
        self.last_message_time = time.time()

    def setJoinedTime(self, new_date):
        self.date = (new_date, self.date[1], self.date[2])

    def calc_acc(self):
        r = self.role
        self.access = aDesc.get(r[0], 0) + aDesc.get(r[1], 0)

    def __str__(self):
        return "%s: %s; last_msg: %d; joined: %s" % (
            self.nick, self.source,
            int(self.last_message_time),
            strfTime(fmt="%d.%m.%Y %H:%M:%S", local=True))


class sConf:
    """Merepresentasikan MUC room."""

    def __init__(self, name, disp, code=None,
                 cPref=None, nick=None, added=False):
        self.name    = name
        self.disp    = disp
        self.nick    = nick or DefNick
        self.code    = code
        self.more    = ""
        self.desc    = {}        # nick -> sUser
        self.IamHere = None
        self.isModer = True
        self.sdate   = 0
        self.alist   = {}
        self.oCmds   = []
        self.cPref   = cPref
        self.status  = DefStatus
        self.state   = sList[0]
        if not added:
            self.save()

    def load_all(self):
        call_sfunctions("01si", (self.name,))

    isHere    = lambda self, nick: (nick in self.desc)
    isHereTS  = lambda self, nick: (self.desc[nick].ishere if self.isHere(nick) else False)
    get_user  = lambda self, nick: self.desc.get(nick)
    isHe      = lambda self, nick, source: (source == self.desc[nick].source)
    get_nicks = lambda self: list(self.desc.keys())
    get_users = lambda self: list(self.desc.values())

    def sorted_users(self):
        for nick in sorted(self.desc):
            user = self.get_user(nick)
            if user:
                yield user

    def sjoined(self, nick, role, source, stanza_info, handle=True):
        # --- Cek Galist / alist dengan JID (source) ---
        access = Galist.get(source) if source else None
        if access is None and source:
            access = self.alist.get(source)

        # --- JID tidak diketahui (bot bukan mod di room) ---
        # Hitung dari affiliation + role supaya owner/admin/moder tetap dapat hak
        if access is None:
            aff, rol = role if isinstance(role, tuple) else (role, role)
            access = aDesc.get(aff, 0) + aDesc.get(rol, 0)

        caps = stanza_info.get("caps", {})
        lang = stanza_info.get("lang", DefLANG).lower().split("_")[0]
        full_jid = stanza_info.get("jid_full", "") or source
        user = self.desc[nick] = sUser(nick, role, source, access, caps, lang, full_jid)

        # Jangan catat bot sendiri ke users.db — bot bukan "member" room
        # yang perlu dilacak join_time-nya.
        is_self = (nick == self.nick) or (source == self.disp)
        if is_self:
            user.date = (time.time(), Yday(), strfTime(local=False))
        else:
            row = runDatabaseQuery(
                "SELECT join_time FROM users WHERE chat=? AND jid=?",
                (self.name, source), many=False)
            if row:
                user.setJoinedTime(row[0])
            elif source:
                runDatabaseQuery(
                    "INSERT INTO users (chat, jid, join_time) VALUES (?, ?, ?)",
                    (self.name, source, user.date[0]), set=True)
        if handle:
            call_efunctions("04eh", (self.name, nick, source, role, stanza_info, self.disp))

    def aroles_change(self, nick, role, stanza_info):
        user = self.get_user(nick)
        new_full = stanza_info.get("jid_full", "")
        if new_full:
            user.full_jid = new_full
        if user.aroles(role):
            if user.source not in Galist and user.source not in self.alist:
                user.calc_acc()
            call_efunctions("07eh", (self.name, nick, role, self.disp))
        else:
            call_efunctions("08eh", (self.name, nick, stanza_info, self.disp))

    def set_nick(self, old_nick, nick):
        self.desc[nick] = self.desc.pop(old_nick)
        self.desc[nick].nick = nick
        call_efunctions("06eh", (self.name, old_nick, nick, self.disp))

    def sleaved(self, nick):
        if nick in self.desc:
            self.desc[nick].ishere = False

    def join(self):
        for user in self.get_users():
            user.ishere = False
        self.sdate = time.time()
        if self.disp in Clients:
            Clients[self.disp].nx_join_muc(self.name, self.nick, self.code)

    def leave(self, exit_status=None):
        self.IamHere = None
        self.isModer = True
        self.more    = ""
        if self.disp in Clients:
            Clients[self.disp].nx_leave_muc(self.name, self.nick, exit_status)

    def full_leave(self, status=None):
        self.leave(status)
        if self.name in Chats:
            del Chats[self.name]
        self.save_stats()
        self.save(False)
        call_sfunctions("04si", (self.name,))
        ChatsAttrs.pop(self.name, None)

    def save_stats(self):
        call_sfunctions("03si", (self.name,))

    def subject(self, body):
        Info["omsg"].plus()
        if self.disp in Clients:
            Clients[self.disp].nx_send_subject(self.name, body)

    def set_status(self, state, status):
        self.state, self.status = state, status

    def change_status(self, state, status):
        self.set_status(state, status)
        if self.disp in Clients:
            Clients[self.disp].nx_send_presence(
                pto="%s/%s" % (self.name, self.nick),
                pshow=state, pstatus=status)

    def save(self, real_save=True):
        if initialize_file(ChatsFile):
            try:
                raw  = get_file(ChatsFile)
                desc = eval(raw) if raw.strip() else {}
            except Exception:
                desc = {}
            if not real_save:
                desc.pop(self.name, None)
            else:
                desc[self.name] = {
                    "disp":       self.disp,
                    sBase[12]:    self.nick,
                    "cPref":      self.cPref,
                    "code":       self.code
                }
            serialised = str(desc)
            cat_file(ChatsFileBackup, serialised)
            cat_file(ChatsFile, serialised)
        else:
            delivery(self.name)

    # MUC affiliation / role shortcuts
    def outcast(self, jid, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_affiliation(self.name, jid, aRoles[1], reason)

    def none(self, jid, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_affiliation(self.name, jid, aRoles[2], reason)

    def member(self, jid, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_affiliation(self.name, jid, aRoles[3], reason)

    def admin(self, jid, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_affiliation(self.name, jid, aRoles[4], reason)

    def owner(self, jid, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_affiliation(self.name, jid, aRoles[5], reason)

    def kick(self, nick, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_role(self.name, nick, aRoles[2], reason)

    def visitor(self, nick, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_role(self.name, nick, aRoles[7], reason)

    def participant(self, nick, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_role(self.name, nick, aRoles[8], reason)

    def moder(self, nick, reason=""):
        if self.disp in Clients:
            Clients[self.disp].nx_set_role(self.name, nick, aRoles[9], reason)

# ── Presence Handler ───────────────────────────────────────────

def _handle_presence(disp_key, presence):
    """
    Dipanggil dari thread pool — menangani MUC presence.
    """
    try:
        pfrom    = presence["from"]
        conf     = str(pfrom.bare).lower()
        nick     = str(pfrom.resource)
        status   = presence.get("status", "")

        # slixmpp: presence["type"] bisa berisi <show> value (chat/away/dnd/xa)
        # ketika presence punya <show> tanpa atribut type="...".
        # Availability sebenarnya: "unavailable" dan "error" eksplisit,
        # selain itu (termasuk "available", "chat", "away", "dnd", "xa") = available.
        raw_type = presence["type"]
        if raw_type in ("unavailable", "error"):
            ptype = raw_type
        else:
            ptype = "available"

        # slixmpp: parse MUC item langsung dari XML — paling reliable
        # <x xmlns="muc#user"><item affiliation="..." role="..." jid="..."/></x>
        role, aff, jid_raw = "none", "none", ""
        try:
            ns   = "http://jabber.org/protocol/muc#user"
            item = presence.xml.find(".//{%s}item" % ns)
            if item is not None:
                role    = item.get("role",        "none") or "none"
                aff     = item.get("affiliation", "none") or "none"
                jid_raw = item.get("jid",         "")    or ""
        except Exception:
            pass

        jid_bare = str(JID(jid_raw).bare).lower() if jid_raw else ""
        # jid_raw biasanya sudah berisi resource (user@host/resource) dari
        # MUC presence <item jid="..."/> — simpan utuh untuk target IQ
        # (vcard/time/version/ping), karena banyak server tidak merespons
        # IQ ke bare JID tapi merespons ke full JID+resource.
        jid_full = jid_raw.lower() if jid_raw else ""

        role_tuple  = (aff, role)
        stanza_info = {
            "caps": {},
            # Baca <lang/> dari presence (XEP-0115).  Sebelumnya di-hardcode
            # DefLANG, jadi getLang() selalu balik default untuk semua user
            # dan pilihan bahasa per-user tidak pernah berjalan.
            "lang": _presence_lang(presence, DefLANG),
            "raw":  presence,
            "status_codes": [],
            "jid_full": jid_full,
        }

        if conf not in Chats:
            return

        Chat = Chats[conf]

        # ── Presence error (ptype = "error") ─────────────────────────
        # Dari BlackSmith: handle error stanza di presence (mis. 409 conflict,
        # 404 not found, 503 service unavailable, 403 forbidden)
        if ptype == "error":
            try:
                ns_err = "urn:ietf:params:xml:ns:xmpp-stanzas"
                xml    = presence.xml
                # Cari error code dari atribut <error code="...">
                err_el = xml.find(".//error")
                ecode  = err_el.get("code", "") if err_el is not None else ""
                if ecode == "409":
                    # Conflict — nick sudah dipakai, tambahkan titik (seperti BlackSmith)
                    Chat.nick = "%s." % nick
                    Chat.join()
                elif ecode in ("404", "503"):
                    # Room tidak ditemukan / service unavailable — schedule rejoin
                    Chat.IamHere = False
                    timer_name = "ejoin-%s" % conf
                    composeTimer(360, lambda c=conf: Chats.get(c) and Chats[c].join(),
                                 timer_name).start()
                    delivery(AnsBase[20] % (ecode, eCodesDesc.get(ecode, ecode), conf))
                elif ecode == "403":
                    # Forbidden — full leave
                    Chat.full_leave(eCodesDesc.get(ecode, ecode))
                    delivery(AnsBase[21] % (ecode, eCodesDesc.get(ecode, ecode), conf))
                elif ecode in ("401", "405"):
                    # Not authorized / not allowed — leave
                    Chat.leave(eCodesDesc.get(ecode, ecode))
                    delivery(AnsBase[22] % (ecode, eCodesDesc.get(ecode, ecode), conf))
            except Exception:
                exc_info_()
            return

        if ptype == "available":
            if Chat.nick == nick:
                Chat.IamHere = True

            if not jid_bare and nick:
                if Chat.isModer:
                    Chat.isModer = False
                    if not Mserve:
                        Chat.change_status(sList[2], "No moderator rights")
                        Message(conf, "Warning: I have no moderator rights here.", disp_key)
                        return
                elif not Mserve:
                    return
            else:
                if not Chat.isModer and Chat.nick == nick and aDesc.get(aff, 0) > 1:
                    Chat.isModer = True
                    Chat.leave("Rejoining with moderator rights...")
                    sleep(0.4)
                    Chat.join()
                    return

            if Chat.isHereTS(nick):
                # User sudah ada — update role/aff saja, tidak perlu JID
                Chat.aroles_change(nick, role_tuple, stanza_info)
            else:
                Chat.sjoined(nick, role_tuple, jid_bare, stanza_info)

        elif ptype == "unavailable":
            status_codes = stanza_info.get("status_codes", [])

            if Chat.nick == nick and ("301" in status_codes or "307" in status_codes):
                sc = "301" if "301" in status_codes else "307"
                Chat.full_leave(sCodesDesc.get(sc, sc))
                delivery(gAnsBase[47] % (conf, sc, sCodesDesc.get(sc, "")))
                return

            if "303" in status_codes:
                new_nick_el = presence.xml.find(
                    ".//{http://jabber.org/protocol/muc#user}item")
                new_nick = new_nick_el.get("nick", "") if new_nick_el is not None else ""
                if new_nick and Chat.isHere(nick):
                    Chat.set_nick(nick, new_nick)
                return

            if Chat.isHereTS(nick):
                Chat.sleaved(nick)
            scode = next((sc for sc in status_codes if sc in sCodes), None)
            call_efunctions("05eh", (conf, nick, status, scode, disp_key))

        call_efunctions("02eh", (presence, disp_key))

    except Exception:
        collectExc(_handle_presence)

# ── Message Handler ────────────────────────────────────────────

def _set_reply_lang(conf, nick, source=None):
    """Pasang bahasa reply untuk thread ini berdasarkan bahasa user."""
    if LocalizationContext is None:
        return
    try:
        # getLang() menerima tuple (source, conf, nick) - bentuk yang sama
        # dengan `source` di dispatcher - atau string conf saja.
        LocalizationContext.set(getLang((source, conf, nick)))
    except Exception:
        # Reply locale bukan fitur kritis; kalau tidak bisa menentukan
        # bahasa user, pakai default saja dan jangan ganggu pemrosesan.
        try:
            LocalizationContext.reset()
        except Exception:
            pass


def _handle_message(disp_key, msg):
    """
    Dipanggil dari thread pool — menangani pesan chat & groupchat.
    """
    try:
        mtype = msg["type"]
        pfrom = msg["from"]

        if mtype == "groupchat":
            conf = str(pfrom.bare).lower()
            nick = str(pfrom.resource)
            inst = conf
        else:
            conf = None
            inst = str(pfrom.bare).lower()
            nick = str(pfrom.resource)

        source = str(pfrom)
        stype  = sBase[1] if mtype == "groupchat" else sBase[0]
        isConf = (inst in Chats)

        if msg.get("delay") and msg["delay"]["stamp"]:
            return

        if isConf:
            Chat    = Chats[inst]
            botNick = Chat.nick
            if not Mserve and not Chat.isModer:
                return
            # Cek access minimum di room (role visitor/none = 0, block spam)
            # tapi owner/admin/moderator/member/participant tetap lolos
            if not enough_access(inst, nick, 0):
                return
        else:
            botNick = DefNick
            # Private chat — inst = JID bare pengirim, cek langsung ke Galist
            bare_sender = inst.lower()
            priv_access = Galist.get(bare_sender, 2)
            if priv_access < 7:
                if not Roster["on"]:
                    return
                checkFlood(disp_key)

        if nick == botNick:
            return

        subject = msg.get("subject", "")
        body    = msg.get("body", "")

        if subject:
            body = subject.strip()
        if not body:
            return

        if isConf:
            user = Chat.get_user(nick)
            if user:
                user.updateLastMessageTime()

        # Bahasa untuk reply di thread ini.  Dipasang di sini (bukan di
        # Answer/Message) karena string AnsBase dievaluasi di call site
        # SEBELUM Answer() dipanggil - memasang di dalam Answer() sudah
        # terlambat.  Context ini hanya untuk satu pesan; thread pool
        # memakai thread baru per pesan, jadi tidak menetes ke pesan lain.
        _set_reply_lang(conf, nick, source)

        if len(body) > IncLimit:
            body = "%s[...] %d symbols limit." % (body[:IncLimit].strip(), IncLimit)

        if mtype == "error":
            code = msg.get("error", {}).get("code", "")
            if code in ("501", "404"):
                if code == "404" and isConf:
                    Chat.join()
                    sleep(0.6)
                Message(source, body)
            return

        if subject:
            call_efunctions("09eh", (inst, nick, subject, body, disp_key))
            return

        temp, isToBs = body, (stype == sBase[0])

        if mtype != "groupchat":
            stype = sBase[0]

        for app in [botNick + sep for sep in (":", ",", ">")]:
            if temp.startswith(app):
                temp, isToBs = temp[len(app):].lstrip(), True
                break

        if not temp:
            return

        parts   = temp.split(None, 1)
        if not parts:
            return
        command = parts.pop(0).lower()
        temp    = parts[0] if parts else ""

        if not isToBs and isConf and Chat.cPref and command not in sCmds:
            if command.startswith(Chat.cPref):
                command = command[1:]
            else:
                command = None
        elif isToBs and command not in Cmds and \
             ((command, inst) not in Macro) and command.startswith(cPrefs):
            command = command[1:]

        if isConf and command in Chat.oCmds:
            return

        Macro(inst, isConf, command, stype, source, nick, temp, disp_key)

        source_tuple = (source, inst, nick)
        if command and command in Cmds:
            VarCache["action"] = "Executing: %s" % command.capitalize()
            VarCache["idle"]   = time.time()
            Cmds[command].execute(stype, source_tuple, temp, disp_key)
        else:
            call_efunctions("01eh",
                (msg, isConf, stype, source_tuple, body, isToBs, disp_key))

    except NodeProcessed:
        pass
    except Exception:
        collectExc(_handle_message)

# ── Command System ─────────────────────────────────────────────

class Command:
    def __init__(self, inst, default, name, access, help_text, exp, lang=None):
        self.exp         = exp
        self.default     = default
        self.name        = name
        self.numb        = AtomicNumber()
        self.isAvailable = True
        self.help        = help_text
        self.handler     = inst
        self.desc        = set()
        self.access      = access
        self.lang        = lang

    def reload(self, inst, access, help_text, exp):
        self.exp         = exp
        self.isAvailable = True
        self.handler     = inst
        self.help        = help_text
        self.access      = access

    def off(self):
        self.isAvailable = False
        self.handler     = None

    def execute(self, stype, source, body, disp):
        answer = None
        if enough_access(source[1], source[2], self.access):
            if self.isAvailable and self.handler:
                Info["cmd"].plus()
                _Log("cmd %s dari %s di %s" % (self.name, source[2], source[1]), logging.INFO)
                sThread("command", self.handler,
                        (self.exp, stype, source, body, disp), self.name)
                self.numb.plus()
                src = get_source(source[1], source[2])
                if src:
                    self.desc.add(src)
            else:
                answer = gAnsBase[48] % self.name
        else:
            answer = gAnsBase[49]
        if answer:
            Answer(answer, stype, source, disp)


def command_handler(exp_inst, handler, default, access, prefix=True):
    name = default
    lang = DefLANG.lower()
    # Help file: expansions/<exp_name>/<command>.<lang>  (contoh: config/config.en)
    help_text = os.path.join(ExpsDir, exp_inst.name, "%s.%s" % (default, lang))
    if not os.path.isfile(help_text):
        # Fallback ke .en jika bahasa default tidak punya file help
        fallback = os.path.join(ExpsDir, exp_inst.name, "%s.en" % default)
        if os.path.isfile(fallback):
            help_text = fallback
    if name not in Cmds:
        Cmds[name] = Command(handler, default, name, access, help_text, exp_inst, lang)
    else:
        Cmds[name].reload(handler, access, help_text, exp_inst)
    if not prefix and name not in sCmds:
        sCmds.append(name)
    exp_inst.cmds.append(name)

# ── Expansion System ───────────────────────────────────────────

class expansion:
    commands = ()
    handlers = ()

    def __init__(self, name):
        self.name  = name
        self.path  = os.path.join(ExpsDir, name)
        self.file  = os.path.join(self.path, "code.py")
        self.isExp = os.path.isfile(self.file)
        self.cmds  = []
        self.desc  = {}

    def initialize_exp(self):
        expansions[self.name] = self
        for ls in self.commands:
            command_handler(self, *ls)
        for inst, ls in self.handlers:
            self.handler_register(getattr(self, inst.__name__), ls)

    auto_clear = None

    def dels(self, full=False):
        while self.cmds:
            cmd = self.cmds.pop()
            if cmd in Cmds:
                Cmds[cmd].off()
        self.clear_handlers()
        self.commands = ()
        self.handlers = ()
        if self.auto_clear:
            try:
                self.auto_clear()
            except Exception:
                pass
        if full and self.name in expansions:
            del expansions[self.name]

    def clear_handlers(self, handler=None):
        def Del(inst, ls):
            if ls == "03si":
                try:
                    inst()
                except Exception:
                    pass
            self.del_handler(ls, inst)
            lst = self.desc[ls]
            lst.remove(inst)
            if not lst:
                del self.desc[ls]

        if handler:
            for ls, lst in sorted(self.desc.items()):
                for inst in lst[:]:
                    if inst == handler:
                        Del(inst, ls)
                        return
        else:
            for ls, lst in sorted(self.desc.items()):
                for inst in lst[:]:
                    Del(inst, ls)

    def initialize_all(self):
        for ls, lst in sorted(self.desc.items()):
            if not ls.endswith("si"):
                continue
            for inst in lst:
                if ls in ("00si", "02si"):
                    try:
                        inst()
                    except Exception:
                        pass
                elif ls == "01si":
                    for conf in list(Chats.keys()):
                        try:
                            inst(conf)
                        except Exception:
                            pass

    def load(self):
        if self.name in expansions:
            expansions[self.name].dels()
        try:
            g = {**globals()}
            insc_file = os.path.join(self.path, "insc.py")
            if os.path.isfile(insc_file):
                try:
                    exec(open(insc_file, encoding="utf-8").read(), g)
                    AnsBase_temp = g.get("AnsBase_temp")
                except Exception:
                    AnsBase_temp = None
            else:
                AnsBase_temp = None
            exec(open(self.file, encoding="utf-8").read(), g)
            exp_inst = g.get("expansion_temp", lambda n: None)(self.name)
            if exp_inst:
                # `insc.py` boleh meng-override AnsBase (mis. versi RU/UA
                # saat DefLANG tertentu).  Kalau ekspansi tidak punya
                # `insc.py`, pakai AnsBase milik code.py sendiri supaya
                # file locale ans.<lang>.json tetap terbaca - dulu
                # ekspansi tanpa `insc.py` tidak pernah ke-wrap sama
                # sekali, jadi locale-nya mati total.
                # Bungkus tuple polos jadi LocalizedAnswers supaya
                # `self.AnsBase[i]` tetap jalan (kode ekspansi existing
                # tidak berubah) tapi bisa memilih string per bahasa.
                # Kalau kelasnya tidak tersedia, jatuh ke tuple biasa.
                base = AnsBase_temp or getattr(exp_inst, "AnsBase", None)
                if base:
                    exp_inst.AnsBase = _wrap_answers(base,
                                                     self.name, self.path)
        except Exception:
            exc_info_()
            return (None, exc_info())
        return (exp_inst, ())

    def add_handler(self, ls, inst):
        if inst not in Handlers[ls]:
            Handlers[ls].append(inst)

    def del_handler(self, ls, inst):
        if inst in Handlers[ls]:
            Handlers[ls].remove(inst)

    def handler_register(self, inst, ls):
        name = inst.__name__
        for existing in Handlers[ls]:
            if name == existing.__name__:
                self.del_handler(ls, existing)
        self.add_handler(ls, inst)
        self.desc.setdefault(ls, []).append(inst)


def load_expansions():
    if not os.path.isdir(ExpsDir):
        PrintWarn("No expansions directory found (%s), skipping." % ExpsDir)
        return (0, 0)
    ok_count  = 0
    err_count = 0
    failed    = []
    for expDir in sorted(os.listdir(ExpsDir)):
        if expDir.startswith(".") or not os.path.isdir(os.path.join(ExpsDir, expDir)):
            continue
        exp = expansion(expDir)
        if exp.isExp:
            inst, exc = exp.load()
            if inst:
                try:
                    inst.initialize_exp()
                    ok_count += 1
                    _Log("expansion loaded: %s" % expDir, logging.DEBUG)
                except Exception:
                    exc_info_()
                    inst.dels(True)
                    failed.append("%s (init failed)" % expDir)
                    err_count += 1
            else:
                failed.append("%s (load failed)" % expDir)
                err_count += 1
        else:
            _Log("expansion skipped (disabled): %s" % expDir, logging.DEBUG)
    # Ringkas: satu baris jumlah, plus daftar hanya yang gagal.
    _Log("expansions: %d loaded%s"
         % (ok_count, ", %d failed" % err_count if err_count else ""),
         logging.INFO)
    for f in failed:
        PrintWarn("  %s" % f)
    return (ok_count, err_count)


# ── Macro (stub) ───────────────────────────────────────────────

class _MacroStub:
    __call__     = lambda self, *a: None
    __contains__ = lambda self, a: False

Macro = _MacroStub()

# ── Connection ─────────────────────────────────────────────────

def connect_client(inst, attrs):
    """
    Construct setelah NxLoop jadi current loop (jebakan slixmpp-gotchas #1),
    connect disubmit ke shared NxLoop. Blocking sampai session_start/timeout.

    Guard anti-storm: maksimal satu percobaan connect per JID dalam satu
    waktu.  Permintaan ganda dijawab (False, CC_CONNECTING) — BUKAN sukses.
    Menjawab True di sini membuat reverseDisp keluar loop dan
    connectAndDispatch langsung conf.join() pada sesi yang belum pernah
    terbentuk.  NexusClient kedua dengan resource sama juga memicu bentrok
    resource di server dan mereproduksi reconnect-storm.
    """
    with _RECONN_LOCK:
        if inst in _CONNECTING:
            # CONNECTING, bukan CONNECTED. Mengembalikan True di sini
            # adalah bug: reverseDisp akan keluar loop dan
            # connectAndDispatch langsung conf.join() pada sesi yang
            # belum pernah terbentuk.
            _reconn_log("[reconn] connect rejected jid=%s: another attempt "
                        "in progress (CC_CONNECTING)", inst)
            return (False, CC_CONNECTING)
        _CONNECTING.add(inst)
    try:
        return _connect_client_body(inst, attrs)
    finally:
        with _RECONN_LOCK:
            _CONNECTING.discard(inst)


def _connect_client_body(inst, attrs):
    (server, cport, host, user, password) = attrs
    PrintInfo('"%s" connecting...' % inst)
    try:
        loop = globals().get("NxLoop")
        if loop is None:
            PrintErr('"%s" no shared loop (NxLoop belum start).' % inst)
            return (False, CC_FAILED)
        asyncio.set_event_loop(loop)
        client = NexusClient(inst, password, server, cport, GenResource)
        client._nx_token = _new_client_token()  # penanda sesi, buat guard
        client.enable_starttls = ConTls
        client.enable_direct_tls = False
        client.enable_plaintext = False

        ready   = threading.Event()
        failed  = threading.Event()

        _orig_start = client._on_session_start
        async def _patched_start(event):
            await _orig_start(event)
            ready.set()

        client.del_event_handler("session_start", client._on_session_start)
        client.add_event_handler("session_start", _patched_start)

        _orig_disc = client._on_disconnected
        async def _patched_disc(event):
            await _orig_disc(event)
            if not ready.is_set():
                failed.set()

        client.del_event_handler("disconnected", client._on_disconnected)
        client.add_event_handler("disconnected", _patched_disc)

        async def _do_connect():
            try:
                await client.connect(host=server, port=cport)
                await client.wait_until("session_start", timeout=40)
            except Exception as e:
                PrintErr('"%s" connect() error: %s' % (inst, e))
                failed.set()

        asyncio.run_coroutine_threadsafe(_do_connect(), loop)

        which = None
        for _ in range(80):
            if ready.is_set():
                which = "ready"
                break
            if failed.is_set():
                which = "failed"
                break
            sleep(0.5)

        if which == "ready":
            token = client._nx_token
            with _RECONN_LOCK:
                # Tandai klien baru SAH lebih dulu, sebelum klien lama
                # di-disconnect.  Kalau urutannya kebalik, handler
                # _on_disconnected klien lama masih dianggap sah dan
                # menjadwalkan timer reconnect tambahan.
                _CLIENT_TOKEN[inst] = token
            _cancel_reconn(inst)            # buang timer yatim klien lama
            old = Clients.get(inst)
            Clients[inst] = client
            _NX_RECONNECT_DELAY.pop(inst, None)
            if old is not None and old is not client:
                # Kunci untuk menafsirkan peristiwa 18.10 00:02:51:
                # "disconnected" tepat setelah "authenticated" berarti
                # teardown klien LAMA (wajar), bukan klien baru gagal.
                _reconn_log("[reconn] old client torn down jid=%s "
                            "old_token=%s new_token=%s",
                            inst, getattr(old, "_nx_token", None), token)
                try:
                    # Tutup sesi lama dengan rapi; efek sampingnya aman
                    # karena tokennya sudah tidak sah (lihat di atas).
                    old.nx_disconnect()
                except Exception:
                    pass
            _reconn_log("[reconn] success jid=%s token=%s (backoff reset)",
                        inst, token)
            PrintOK('"%s" connected and authenticated!' % inst)
            return (True, CC_CONNECTED)
        else:
            PrintErr('"%s" failed to establish session (timeout/error).' % inst)
            try:
                client.nx_disconnect()
            except Exception:
                pass
            return (False, CC_FAILED)

    except Exception as e:
        PrintErr('"%s" connection error: %s' % (inst, e))
        exc_info_()
        return (False, CC_FAILED)


def reverseDisp(disp, rejoin=True):
    # Guard anti-storm: koneksi sudah sehat -> jangan buat klien baru.
    cur = Clients.get(disp)
    if cur is not None and cur.isConnected():
        _reconn_log("[reconn] reverseDisp jid=%s -> skipped, already connected",
                    disp)
        return True
    _reconn_log("[reconn] reverseDisp jid=%s started", disp)
    for i in range(1440):
        ok, status = connect_client(disp, InstancesDesc[disp])
        _reconn_log("[reconn] reverseDisp jid=%s attempt %d -> %s",
                    disp, i + 1, status)
        if ok and status == CC_CONNECTED:
            # Hanya CC_CONNECTED yang dianggap berhasil. CC_CONNECTING
            # (connect lain sedang berjalan untuk JID yang sama) dihitung
            # belum berhasil, jadi loop jatuh ke sleep(60) berikutnya —
            # memakai loop yang sudah ada, tanpa loop tunggu atau timer
            # baru yang bisa memicu reconnect-storm.
            cur = Clients.get(disp)
            if rejoin and cur is not None and cur.isConnected():
                for conf in list(Chats.values()):
                    if conf.disp == disp:
                        conf.join()
            return True
        sleep(60)
    _reconn_log("[reconn] reverseDisp jid=%s FAILED after 1440 attempts",
                disp)
    return False


def connectAndDispatch(disp):
    if reverseDisp(disp, False):
        sleep(60)
        # Sinkronkan dulu: reverseDisp boleh saja sukses, tapi sesi bisa
        # belum aktif (CONNECTING) atau sudah putus lagi di tengah
        # sleep(60). Join hanya kalau sesi yang sama benar-benar hidup.
        cur = Clients.get(disp)
        if cur is None or not cur.isConnected():
            delivery('"%s" failed to reconnect.' % disp)
            return
        for conf in Chats.values():
            if disp == conf.disp:
                conf.join()
    else:
        delivery('"%s" failed to reconnect.' % disp)


def connect_clients():
    for inst, attrs in list(InstancesDesc.items()):
        ok, result = connect_client(inst, attrs)
        if not ok:
            composeTimer(60, connectAndDispatch,
                         "%s-%s" % (sBase[13], inst), (inst,)).start()

# ── Session & Chat Loading ─────────────────────────────────────

def check_copies():
    cache = base = {"PID": NxPid, "up": Info["sess"], "alls": []}
    if os.path.isfile(PidFile):
        try:
            cache = eval(get_file(PidFile))
        except SyntaxError:
            del_file(PidFile)
        except Exception:
            pass
        else:
            try:
                if NxPid == cache["PID"]:
                    # PID sama = soft-reload via Exit()/os.execl()
                    # → pertahankan "up" lama, catat reload ini ke "alls"
                    cache["alls"].append(strfTime())
                else:
                    # PID berbeda = proses baru (start manual / restart penuh)
                    # → bunuh proses lama (jika masih hidup), lalu RESET
                    #   "up" dan "alls" karena ini adalah boot baru, bukan
                    #   lanjutan sesi lama.
                    if OSList.windows:
                        # /fi IMAGENAME filter agar tidak error jika PID tidak ada
                        # >nul 2>&1 suppress output "not found"
                        ret = os.system(
                            "TASKKILL /PID %d /T /f >nul 2>&1" % cache["PID"])
                        if ret != 0:
                            PrintInfo("Old PID %d already gone (Windows)." % cache["PID"])
                    else:
                        try:
                            os.kill(cache["PID"], 15)
                            sleep(2)
                            try:
                                os.kill(cache["PID"], 9)
                            except ProcessLookupError:
                                pass
                        except ProcessLookupError:
                            pass
                    cache = base
            except Exception:
                cache = base
    cat_file(PidFile, str(cache))
    cache.pop("PID", None)
    Info.update(cache)



def join_chats():
    if initialize_file(ChatsFile):
        try:
            confs = eval(get_file(ChatsFile))
        except Exception:
            confs = {}
        Print("rooms: %d" % len(confs), color6)
        for conf, desc in confs.items():
            Chats[conf] = Chat = sConf(conf, added=True, **desc)
            Chat.load_all()
            if Chat.disp in Clients:
                Chat.join()
                PrintOK("%s  →  %s" % (Chat.disp, conf))
            else:
                PrintWarn("Pending %s  (waiting for %s)" % (conf, Chat.disp))
    else:
        PrintErr("Can't create chats file!")

# ── Main Startup ───────────────────────────────────────────────

def load_nexsus():
    if not os.path.exists(args.dynamic):
        os.makedirs(args.dynamic, exist_ok=True)

    _print_banner()

    global AnsBase, NxLoop
    insc_path = static % "insc.py"
    if os.path.isfile(insc_path):
        try:
            g2 = {"DefLANG": DefLANG}
            exec(open(insc_path, encoding="utf-8").read(), g2)
            if "AnsBase" in g2:
                # Bungkus juga tabel global. Enam ekspansi (alias, dns, muc,
                # extra_control, roster_control, session_stats) tidak punya
                # AnsBase sendiri dan jatuh ke tabel ini, jadi tanpa pembungkus
                # :subject / :ban / :kick / :turbo tetap keluar dalam bahasa
                # Rusia apa pun bahasa aktif user.
                AnsBase = _wrap_answers(g2["AnsBase"], "__global__",
                                        os.path.dirname(insc_path))
                # Alias yang dijamin tidak pernah ter-shadow. Ekspansi yang
                # punya AnsBase sendiri meng-assign `AnsBase` ke namespace-nya
                # saat exec(), jadi `AnsBase[N]` di dalam ekspansi itu menunjuk
                # tabel LOKAL, bukan global. Call site yang memang butuh tabel
                # global harus pakai `gAnsBase`.
                globals()["gAnsBase"] = AnsBase
        except Exception:
            exc_info_()
            PrintWarn("Could not load static/insc.py")

    runDatabaseQuery(
        "CREATE TABLE IF NOT EXISTS users "
        "(chat TEXT, jid TEXT, join_time INTEGER)",
        set=True)

    check_copies()
    ok_count, err_count = load_expansions()
    call_sfunctions("00si")
    # Satu shared loop (pola xmpp-platform). Client di-construct SETELAH
    # ini di main thread, jadi Future internal nempel ke loop yang benar.
    NxLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(NxLoop)
    def _run_nx_loop():
        asyncio.set_event_loop(NxLoop)
        NxLoop.run_forever()
    threading.Thread(target=_run_nx_loop, name="NxLoop", daemon=True).start()
    connect_clients()

    waited = 0
    while not any(c.isConnected() for c in Clients.values()) and waited < 40:
        sleep(0.5)
        waited += 0.5

    if not any(c.isConnected() for c in Clients.values()):
        PrintWarn("No clients connected yet, continuing anyway...")

    PrintOK("Nexus is online!")
    join_chats()
    _print_startup_summary(ok_count, err_count)

    _Log("%s is running. Press Ctrl+C to stop." % ProdName, logging.INFO)

    call_sfunctions("02si")


    # Main loop — monitoring
    last_seen_connected = time.time()
    while VarCache["alive"]:
        sleep(180)
        connected = sum(1 for c in Clients.values() if c.isConnected())
        if connected:
            last_seen_connected = time.time()
        elif Clients and (time.time() - last_seen_connected) > 600:
            sys_exit("All clients down for over 10 minutes!")
        gc.collect()
        if MaxMemory:
            try:
                import resource
                mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                if mem >= MaxMemory:
                    sys_exit("Memory limit exceeded!")
            except Exception:
                pass


def sys_exit(reason="Shutdown", restart=True):
    VarCache["alive"] = False
    # INFO, bukan WARNING: shutdown karena Ctrl+C adalah hal normal,
    # bukan kondisi yang perlu diwaspadai.
    _Log(reason, logging.INFO)
    try:
        call_sfunctions("03si")
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    # Stop shared loop — tanpa memanggil disconnect()
    # OS akan cleanup koneksi saat process restart
    try:
        if NxLoop is not None and NxLoop.is_running():
            NxLoop.call_soon_threadsafe(NxLoop.stop)
    except Exception:
        pass
    try:
        sleep(1)
    except KeyboardInterrupt:
        pass
    if restart:
        Exit("Reloading in 30s...  (Ctrl+C to quit)\n", False, 30)
    else:
        # Jalur berhenti TANPA os.execl — dipakai oleh Ctrl+C.
        # Dulu semua sys_exit berakhir di Exit(..., False, 30) ->
        # os.execl, jadi Ctrl+C melahirkan proses baru 30 detik
        # kemudian dan terbaca sebagai "restart sendiri".
        # Pemanggil lain (watchdog, memory, reload, update, SIGTERM)
        # tetap memakai default restart=True.
        os._exit(0)


if __name__ == "__main__":
    load_config()
    try:
        load_nexsus()
    except KeyboardInterrupt:
        try:
            # restart=False -> os._exit(0): Ctrl+C benar-benar berhenti,
            # bukan reload 30 detik kemudian.
            sys_exit("Interrupted (Ctrl+C)", restart=False)
        except KeyboardInterrupt:
            PrintErr("Force quit.")
            os._exit(0)
    except SystemExit:
        sys_exit("SIGTERM received")
    except Exception:
        collectExc(load_nexsus)
