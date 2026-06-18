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
import sqlite3
import configparser

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

# ── Argument Parser ────────────────────────────────────────────

argParser = ArgumentParser(description="Nexsus Safety XMPP Engine")
argParser.add_argument("-s", "--static",     help="Static folder",    default="static")
argParser.add_argument("-d", "--dynamic",    help="Dynamic folder",   default="current")
argParser.add_argument("-e", "--expansions", help="Expansions folder", default="expansions")
args = argParser.parse_args()

# ── Logger ─────────────────────────────────────────────────────

LOG_LEVEL = logging.DEBUG
logFile   = "nexsus.log"

logger        = logging.getLogger("nexsus")
logger.setLevel(LOG_LEVEL)
loggerHandler = logging.FileHandler(logFile, encoding="utf-8")
formatter     = logging.Formatter(
    "%(asctime)s %(levelname)s: %(name)s: %(message)s",
    "%d.%m.%Y %H:%M:%S")
loggerHandler.setFormatter(formatter)
logger.addHandler(loggerHandler)

# Suppress "Unknown stanza interface: ..." warnings dari slixmpp
# yang muncul di terminal via root logger — tidak ada action yang bisa diambil
# dan warning ini sudah di-handle via XML fallback parse.
class _SlixmppFilter(logging.Filter):
    _suppress = ("Unknown stanza interface:",)
    def filter(self, record):
        msg = record.getMessage()
        return not any(s in msg for s in self._suppress)

logging.getLogger().addFilter(_SlixmppFilter())

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


def Print(text, color=color0):
    print(color + str(text) + color0, flush=True)


def PrintOK(text):
    """Hijau dengan prefix check"""
    print(color3 + "  \u2714  " + str(text) + color0, flush=True)


def PrintWarn(text):
    """Kuning dengan prefix warning"""
    print(color1 + "  \u26a0  " + str(text) + color0, flush=True)


def PrintErr(text):
    """Merah dengan prefix cross"""
    print(color2 + "  \u2718  " + str(text) + color0, flush=True)


def PrintInfo(text):
    """Biru dengan prefix bullet"""
    print(color4 + "  \u25cf  " + str(text) + color0, flush=True)


def PrintDivider():
    """Garis pemisah flat — pengganti border kotak."""
    print(color5 + _hr() + color0, flush=True)


def PrintHeader(title):
    """Header section flat: divider / judul / divider — tanpa kotak."""
    PrintDivider()
    print(color5 + "  " + title + color0, flush=True)
    PrintDivider()


def PrintSection(title):
    """Alias kompatibilitas — section header flat."""
    PrintHeader(title)


# ── Product Identity ───────────────────────────────────────────

(NxMark, NxVer, NxRev) = (1, 0, 1)
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
    """Cetak banner startup Nexsus Safety — flat, auto-fit lebar terminal."""
    import platform as _plt
    py_ver  = "%d.%d.%d" % sys.version_info[:3]
    ver_num = "%d.%d.%d" % (NxMark, NxVer, NxRev)
    started = strfTime("%Y-%m-%d %H:%M:%S")

    PrintDivider()
    print(color5 + "  \U0001f916  %s  v%s" % (ProdName, ver_num) + color0, flush=True)
    PrintDivider()
    print("  Account    : %s" % GenDisp, flush=True)
    print("  Admin      : %s" % GodName, flush=True)
    print("  PID        : %d" % NxPid, flush=True)
    print("  Python     : %s (%s)" % (py_ver, _plt.system()), flush=True)
    print("  Started at : %s" % started, flush=True)


def _print_startup_summary(ok_count, err_count):
    """Cetak ringkasan startup — flat, dipanggil saat tahap READY."""
    n_cmds    = len([c for c in Cmds.values() if c.isAvailable])
    n_rooms   = len(Chats)
    n_clients = sum(1 for c in Clients.values() if c.isConnected())
    n_total   = len(Clients)
    active    = ", ".join(sorted(expansions.keys()))

    PrintHeader("Startup Summary")
    print("  Expansions     : %d loaded, %d failed" % (ok_count, err_count), flush=True)
    print("  Commands       : %d" % n_cmds, flush=True)
    print("  Rooms joined   : %d" % n_rooms, flush=True)
    print("  Clients        : %d / %d connected" % (n_clients, n_total), flush=True)
    print("  Active plugins : %s" % active, flush=True)



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
ExpsDir         = args.expansions
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
    "This command implies arguments using.",              # 1
    "Invalid syntax.",                                    # 2
    "There is no '%s' in the chats-list.",               # 3
    "Done.",                                             # 4
    "Parameters should be shorter.",                     # 5
    "Such command isn't exist.",                         # 6
    "I can't.",                                          # 7
    "There is no such conference in my list.",           # 8
    "Type is invalid.",                                  # 9
    "You need to access higher.",                        # 10
    "You should look into private.",                     # 11
    "# %d. - %s",                                        # 12
    "command '%s' (%s)",                                 # 13
    "prosess '%s'",                                      # 14
    "When execut %s --> error happend!",                 # 15
    "Type --> 'excinfo %d' to show error (crashfile --> %s)", # 16
    "Type --> 'excinfo %d' or 'sh cat %s' to show error",    # 17
    "%s[...]\n\n** %d symbols limit! Type 'more' to show rest.", # 18
    "Command '%s' is unavailable now!",                  # 19
    "Error %s (%s) - conference: '%s'.",                 # 20
    "Error %s (%s), full exit from '%s'.",               # 21
    "Error %s (%s), I leaved '%s'.",                     # 22
    "The service without admin's affilation is unavailable!", # 23
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


def Exit(text, do_exit, slp):
    PrintErr(text)
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
    ext   = []
    units = [
        ("Year",   None),
        ("Day",    365.25),
        ("Hour",   24),
        ("Minute", 60),
        ("Second", 60)
    ]
    t = secs
    while units:
        label, div = units.pop()
        if div:
            t, rest = divmod(t, div)
        else:
            rest = t
        if rest >= 1.0:
            plural = "s" if rest >= 2 else ""
            ext.insert(0, "%d %s%s" % (int(rest), label, plural))
        if not (units and t):
            return " ".join(ext)
    return "0 Seconds"


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

def _get_client_loop(disp):
    """Dapatkan asyncio loop dari NexusClient."""
    key    = disp if isinstance(disp, str) else get_disp(disp)
    client = Clients.get(key)
    if client and hasattr(client, "_loop") and client._loop:
        return client._loop
    for c in Clients.values():
        if hasattr(c, "_loop") and c._loop and c._loop.is_running():
            return c._loop
    return None


def run_coro(coro, disp=None):
    """Jalankan coroutine dari thread manapun secara blocking."""
    loop = _get_client_loop(disp) if disp else None
    if not loop:
        for c in Clients.values():
            lp = getattr(c, "_loop", None)
            if lp and lp.is_running():
                loop = lp
                break
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
    loop = _get_client_loop(disp) if disp else None
    if not loop:
        for c in Clients.values():
            lp = getattr(c, "_loop", None)
            if lp and lp.is_running():
                loop = lp
                break
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(coro, loop)

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


def load_config():
    global GodName, DefNick, DefStatus, GenResource
    global ConTls, Mserve, GetExc, DefLANG
    global IncLimit, PrivLimit, ConfLimit, ChatListLimit, MaxMemory
    global Debug, GenDisp, InstancesDesc, Galist
    global GenCon, ConDisp

    try:
        GenCon = configparser.ConfigParser()
        GenCon.read(GenConFile)
        GenDisp, Instance  = client_config(GenCon, "CLIENT")
        InstancesDesc      = {GenDisp: Instance}
        ConTls             = GenCon.getboolean("STATES", "TLS",    fallback=True)
        Mserve             = GenCon.getboolean("STATES", "MSERVE", fallback=True)
        GetExc             = GenCon.getboolean("STATES", "GETEXC", fallback=True)
        DefLANG            = GenCon.get("STATES", "LANG", fallback="EN").upper()[:2]
        GodName            = GenCon.get("CONFIG", "ADMIN",    fallback="admin@localhost").lower()
        DefNick            = GenCon.get("CONFIG", "NICK",     fallback="NexsusBot").split()[0]
        DefStatus          = GenCon.get("CONFIG", "STATUS",   fallback="Nexus Online")
        GenResource        = GenCon.get("CONFIG", "RESOURCE", fallback="Nexus")
        IncLimit           = int(GenCon.get("LIMITS", "INCOMING",         fallback="2000"))
        PrivLimit          = int(GenCon.get("LIMITS", "PRIVATE",          fallback="2000"))
        ConfLimit          = int(GenCon.get("LIMITS", "CHAT",             fallback="2000"))
        ChatListLimit      = int(GenCon.get("LIMITS", "CHAT_LIST_LENGTH", fallback="100"))
        MaxMemory          = int(GenCon.get("LIMITS", "MEMORY",           fallback="0")) * 1024

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
            True, 2)

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
            composeTimer(60, reverseDisp, "reconn-%s" % self._nx_jid,
                         (self._nx_jid,)).start()
        loop = getattr(self, "_loop", None)
        if loop and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)

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
        """Disconnect dengan cara yang benar untuk versi slixmpp apapun."""
        try:
            loop = getattr(self, "_loop", None)
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
        """Schedule coroutine ke loop asyncio milik client ini."""
        loop = getattr(self, "_loop", None)
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


def getLang(source):
    """
    Dari BlackSmith: ambil bahasa user dari Chats (untuk multi-lang expansion).
    source bisa berupa tuple (source, conf, nick) atau string conf.
    """
    if isinstance(source, (tuple, list)) and len(source) > 2:
        chat = Chats.get(source[1])
        if chat:
            user = chat.get_user(source[2])
            if user:
                return getattr(user, "lang", DefLANG.lower())
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
            "lang": DefLANG,
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
                delivery("Left %s: %s (%s)" % (conf, sc, sCodesDesc.get(sc, "")))
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
            call_efunctions("05eh", (conf, nick, status, None, disp_key))

        call_efunctions("02eh", (presence, disp_key))

    except Exception:
        collectExc(_handle_presence)

# ── Message Handler ────────────────────────────────────────────

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
             (command not in Macro) and command.startswith(cPrefs):
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
                sThread("command", self.handler,
                        (self.exp, stype, source, body, disp), self.name)
                self.numb.plus()
                src = get_source(source[1], source[2])
                if src:
                    self.desc.add(src)
            else:
                answer = "Command '%s' is currently unavailable." % self.name
        else:
            answer = "Access denied."
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
            if exp_inst and AnsBase_temp:
                exp_inst.AnsBase = AnsBase_temp
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
    PrintHeader("Loading Expansions")
    if not os.path.isdir(ExpsDir):
        PrintWarn("No expansions directory found (%s), skipping." % ExpsDir)
        return (0, 0)
    ok_count  = 0
    err_count = 0
    for expDir in sorted(os.listdir(ExpsDir)):
        if expDir.startswith(".") or not os.path.isdir(os.path.join(ExpsDir, expDir)):
            continue
        exp = expansion(expDir)
        if exp.isExp:
            inst, exc = exp.load()
            if inst:
                try:
                    inst.initialize_exp()
                    print(color3 + "  \u2705 " + expDir + color0, flush=True)
                    ok_count += 1
                except Exception:
                    exc_info_()
                    inst.dels(True)
                    print(color2 + "  \u274c %s  (init failed: %s)" % (expDir, exc_info()) + color0, flush=True)
                    err_count += 1
            else:
                print(color2 + "  \u274c %s  (load failed: %s)" % (expDir, exc) + color0, flush=True)
                err_count += 1
        else:
            Print("  \u00b7  %s  (no code.py)" % expDir, color6)
    return (ok_count, err_count)


# ── Macro (stub) ───────────────────────────────────────────────

class _MacroStub:
    __call__     = lambda self, *a: None
    __contains__ = lambda self, a: False

Macro = _MacroStub()

# ── Connection ─────────────────────────────────────────────────

def connect_client(inst, attrs):
    """
    Buat NexusClient dan jalankan di asyncio loop di thread daemon-nya sendiri.
    Blocking sampai session_start atau timeout.
    """
    (server, cport, host, user, password) = attrs
    PrintInfo('"%s" connecting...' % inst)
    try:
        client = NexusClient(inst, password, server, cport, GenResource)

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

        def _run_client():
            """Jalankan client di loop asyncio dedicated per-client."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client._loop = loop

            async def _start():
                # slixmpp 1.15.0 — inspect connect() signature at runtime
                # supaya tidak hardcode parameter yang mungkin berbeda antar versi
                import inspect as _inspect
                try:
                    sig    = _inspect.signature(client.connect)
                    params = set(sig.parameters.keys())
                    kwargs = {}
                    if "host"             in params: kwargs["host"]             = server
                    if "port"             in params: kwargs["port"]             = cport
                    if "use_ssl"          in params: kwargs["use_ssl"]          = False
                    if "force_starttls"   in params: kwargs["force_starttls"]   = ConTls
                    if "disable_starttls" in params: kwargs["disable_starttls"] = not ConTls
                    # Jika tidak ada satupun keyword, pakai positional
                    if not kwargs:
                        await client.connect(server, cport)
                    else:
                        await client.connect(**kwargs)
                except Exception as e:
                    PrintErr('"%s" connect() error: %s' % (inst, e))
                    failed.set()

            try:
                loop.run_until_complete(_start())
                if not failed.is_set():
                    loop.run_forever()
                    try:
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(
                                asyncio.wait(pending, timeout=2))
                    except Exception:
                        pass
            except Exception:
                exc_info_()
                failed.set()
            finally:
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        try:
                            loop.run_until_complete(
                                asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass
                    loop.close()
                except Exception:
                    pass

        t = threading.Thread(target=_run_client,
                             name="NxClient-%s" % inst, daemon=True)
        t.start()

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
            Clients[inst] = client
            PrintOK('"%s" connected and authenticated!' % inst)
            return (True, inst)
        else:
            PrintErr('"%s" failed to establish session (timeout/error).' % inst)
            try:
                client.nx_disconnect()
            except Exception:
                pass
            return (False, None)

    except Exception as e:
        PrintErr('"%s" connection error: %s' % (inst, e))
        exc_info_()
        return (False, None)


def reverseDisp(disp, rejoin=True):
    for _ in range(1440):
        if connect_client(disp, InstancesDesc[disp])[0]:
            if rejoin:
                for conf in list(Chats.values()):
                    if conf.disp == disp:
                        conf.join()
            return True
        sleep(60)
    return False


def connectAndDispatch(disp):
    if reverseDisp(disp, False):
        sleep(60)
        for conf in Chats.values():
            if disp == conf.disp:
                conf.join()
    else:
        delivery('"%s" failed to reconnect.' % disp)


def connect_clients():
    PrintSection("CONNECTIONS")
    for inst, attrs in list(InstancesDesc.items()):
        ok, result = connect_client(inst, attrs)
        if not ok:
            composeTimer(60, connectAndDispatch,
                         "%s-%s" % (sBase[13], inst), (inst,)).start()
    print(flush=True)

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
                            PrintInfo("Old PID %d already gone." % cache["PID"])
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
        PrintSection("ROOMS")
        Print("  %d room(s) in list" % len(confs), color6)
        for conf, desc in confs.items():
            Chats[conf] = Chat = sConf(conf, added=True, **desc)
            Chat.load_all()
            if Chat.disp in Clients:
                Chat.join()
                PrintOK("%s  →  %s" % (Chat.disp, conf))
            else:
                PrintWarn("Pending %s  (waiting for %s)" % (conf, Chat.disp))
        print(flush=True)
    else:
        PrintErr("Can't create chats file!")

# ── Main Startup ───────────────────────────────────────────────

def load_nexsus():
    if not os.path.exists(args.dynamic):
        os.makedirs(args.dynamic, exist_ok=True)

    _print_banner()

    global AnsBase
    insc_path = static % "insc.py"
    if os.path.isfile(insc_path):
        try:
            g2 = {"DefLANG": DefLANG}
            exec(open(insc_path, encoding="utf-8").read(), g2)
            if "AnsBase" in g2:
                AnsBase = g2["AnsBase"]
                PrintOK("AnsBase loaded from static/insc.py")
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

    PrintDivider()
    print(color3 + "  \u25cf  %s is running  \u2014  Press Ctrl+C to stop" % ProdName + color0, flush=True)
    PrintDivider()
    print(flush=True)

    call_sfunctions("02si")


    # Main loop — monitoring
    while VarCache["alive"]:
        sleep(180)
        connected = sum(1 for c in Clients.values() if c.isConnected())
        if not connected and Clients:
            sys_exit("All clients down!")
        gc.collect()
        if MaxMemory:
            try:
                import resource
                mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                if mem >= MaxMemory:
                    sys_exit("Memory limit exceeded!")
            except Exception:
                pass


def sys_exit(reason="Shutdown"):
    VarCache["alive"] = False
    PrintWarn(reason)
    try:
        call_sfunctions("03si")
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    # Stop semua asyncio loop — tanpa memanggil disconnect()
    # OS akan cleanup koneksi saat process restart
    for client in list(Clients.values()):
        try:
            loop = getattr(client, "_loop", None)
            if loop and loop.is_running():
                loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
    try:
        sleep(1)
    except KeyboardInterrupt:
        pass
    Exit("Reloading in 30s...  (Ctrl+C to quit)\n", False, 30)


if __name__ == "__main__":
    load_config()
    try:
        load_nexsus()
    except KeyboardInterrupt:
        try:
            sys_exit("Interrupted (Ctrl+C)")
        except KeyboardInterrupt:
            PrintErr("Force quit.")
            os._exit(0)
    except SystemExit:
        sys_exit("SIGTERM received")
    except Exception:
        collectExc(load_nexsus)
