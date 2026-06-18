# Nexsus Safety

> **Port Python 3 / slixmpp** dari BlackSmith mark.2 (WitcherGeralt)
> Porting Python3 by: paijo.ahmad@jabber.ru

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![slixmpp](https://img.shields.io/badge/XMPP-slixmpp%201.15%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**Versi:** 1.0.0 Core BlackSmith mark.2
**Basis:** Port Python 3 / slixmpp dari BlackSmith mark.2 (WitcherGeralt)
**Protokol:** XMPP (Jabber) — client MUC bot

---

## 1. Ringkasan

Nexsus Safety adalah bot XMPP berbasis arsitektur **expansion** (plugin) — setiap fitur (command, auto-responder, scheduler) adalah modul terpisah yang dimuat otomatis saat startup dari folder `expansions/`. Engine inti (`NexsusBot.py`) menyediakan:

- Koneksi XMPP (multi-account) via **slixmpp**
- Manajemen room MUC (join, roles, affiliations)
- Sistem command dengan prefix dan level akses
- Database SQLite per-fitur
- Sistem help otomatis dari file `.{lang}`

---

## 2. Kerangka / Struktur Folder

```
nexsusBot/
├── NexsusBot.py            # Engine inti — koneksi, presence, command dispatcher
├── requirements.txt        # Dependency Python
├── users.db                 # Database user global (SQLite)
├── nexsus.log                 # Log runtime (DEBUG level)
│
├── static/                   # Konfigurasi & teks statis (TIDAK berubah saat runtime)
│   ├── config.ini            # Config utama: akun, TLS, limit, admin
│   ├── clients.ini            # Akun XMPP tambahan (multi-account)
│   └── insc.py                # AnsBase global (teks jawaban default)
│
├── current/                   # Data dinamis (runtime, per-room/per-user)
│   ├── chats.db / chats.cp    # Daftar room yang diikuti bot
│   ├── access.db              # Daftar access level custom per-JID
│   ├── sessions.db            # PID tracking (cegah duplikat proses)
│   ├── roster.db              # Status roster (on/off)
│   ├── notepad.db             # Data command 'note'
│   ├── wtf.db                  # Data command 'wtf'/'def'
│   ├── books.db / cdesc.db     # Data expansion 'books'
│   └── <room_jid>/             # Folder per-room (data spesifik room)
│
├── library/                    # Library lokal (bukan via pip)
│   ├── itypes.py               # Counter & tipe data util (AtomicNumber dkk)
│   ├── ithr.py                 # Thread helper
│   └── fb2.py                  # Parser FictionBook (expansion 'books')
│
└── expansions/                 # Semua fitur/plugin bot
    └── <nama_expansion>/
        ├── code.py             # Logic command & handler
        ├── insc.py             # Teks jawaban (AnsBase) — opsional, multi-bahasa
        └── <command>.<lang>    # File help, contoh: ping.en, config.en
```

---

## 3. Arsitektur Inti (`NexsusBot.py`)

### 3.1 Komponen Utama

| Komponen | Fungsi |
|---|---|
| `NexusClient` | Wrapper `slixmpp.ClientXMPP` — 1 instance per akun XMPP |
| `sConf` | Representasi 1 room MUC (peserta, status, affiliation) |
| `sUser` | Representasi 1 peserta dalam room (nick, JID, role, access) |
| `Command` | Wrapper 1 command — handler, access level, help, statistik |
| `expansion` | Base class setiap plugin di `expansions/` |
| `Cmds` | Dict global semua command terdaftar |
| `Chats` | Dict global semua room yang diikuti |
| `Clients` | Dict global semua koneksi XMPP aktif |

### 3.2 Siklus Hidup (Startup Flow)

```
load_config()          → baca static/config.ini & clients.ini
  └─ load_nexus()
       ├─ load AnsBase dari static/insc.py
       ├─ check_copies()       → cek PID lama, kill jika masih jalan
       ├─ load_expansions()    → scan & load semua expansions/*/code.py
       ├─ call_sfunctions("00si") → init handler tahap awal
       ├─ connect_clients()    → connect semua akun XMPP
       ├─ join_chats()         → join semua room dari current/chats.db
       └─ Main loop: monitoring tiap 180s (memory, koneksi)
```

### 3.3 Sistem Akses (Access Level)

| Level | Label | Keterangan |
|---|---|---|
| 8 | God | Admin utama (`ADMIN=` di config.ini), akses penuh |
| 7 | Chief | Akses tinggi (private command, remote, dll) |
| 6 | — | Owner/Admin room |
| 5 | — | Moderator room |
| 4 | — | — |
| 3 | — | Participant dengan affiliation member |
| 2 | — | Participant biasa |
| 1 | All | Default — semua user |
| 0 | — | Visitor (read-only di room moderated) |

Access dihitung dari kombinasi `affiliation + role` di room (jika JID tidak diketahui), atau dari `Galist`/`access.db` (jika JID dikenal).

### 3.4 Alur Pesan Masuk

```
_handle_message()
  ├─ Cek access minimum (enough_access)
  ├─ Cek prefix command (! @ # . *  atau nick bot)
  ├─ Parse command + argumen
  ├─ Macro hook (untuk expansion yang intercept semua pesan)
  └─ Cmds[command].execute() → jalankan handler di thread terpisah
```

---

## 4. Daftar Expansion (31 Modul)

| Expansion | Command | Fungsi |
|---|---|---|
| `access` | `access`, `acclist`, `acclist2`, `gaccess`, `laccess` | Manajemen access level user |
| `alive_keeper` | — | Auto-ping berkala agar koneksi tetap hidup |
| `allweb` | — | Helper akses web (internal) |
| `basic_control` | `join`, `rejoin`, `leave`, `reconnect`, `reload`, `exit` | Kontrol koneksi & room |
| `books` | `order` | Pencarian & pengiriman e-book (FictionBook) |
| `bot_sends` | `clear`, `test`, `sendall`, `more`, `send`, `toadmin`, `echo`, `invite` | Kirim pesan massal/khusus |
| `calendar` | `calendar` | Tampilan kalender |
| `clear_stats` | — | Reset statistik saat user/bot keluar room |
| `cmd_control` | `taboo` | Blokir command tertentu per-room |
| `config` | `config`, `client` | Lihat/ubah konfigurasi runtime |
| `converter` | `convert` | Konversi satuan/mata uang |
| `cron` | `cron` | Penjadwalan tugas berkala |
| `dns` | `dns`, `port` | Lookup DNS & cek port |
| `exp_control` | `expinfo`, `expload`, `expunload`, `tumbler` | Manajemen expansion (load/unload runtime) |
| `extra_control` | `turbo`, `remote`, `private`, `redirect` | Eksekusi command lanjutan (multi/remote) |
| `game` | `game` | Mini-game |
| `get_iq` | `ping`, `pstat`, `time`, `version`, `vcard`, `uptime`, `idle`, `list`, `disco` | Query info XMPP (IQ requests) |
| `help` | `location`, `comacc`, `help`, `commands` | Sistem bantuan & info command |
| `info` | `online`, `chatslist`, `inmuc`, `visitors`, `search` | Info status room & user |
| `interpreter` | `eval`, `exec`, `sh`, `calc` | Eksekusi kode/shell (akses tinggi) |
| `muc` | `subject`, `ban`, `none`, `member`, `admin`, `owner`, `kick`, `visitor`, `participant`, `moder`, `fullban`, `fullunban` | Moderasi & administrasi MUC |
| `new_year` | `new_year` | Hitung mundur tahun baru |
| `note` | `note` | Catatan personal per-user |
| `roster_control` | `roster`, `roster2` | Manajemen roster/subscription |
| `sconf_attrs` | `botjid`, `botnick`, `botstatus`, `password`, `prefix` | Atribut bot per-room |
| `session_stats` | `excinfo`, `botup`, `stat`, `comstat` | Statistik sesi & uptime |
| `sheriff` | `order` | Moderasi otomatis |
| `talkers` | `talkers` | Statistik aktivitas user |
| `turn` | `turn` | Sistem giliran/antrian |
| `user_stats` | `userstat`, `here` | Statistik per-user |
| `wtf` | `wtf`, `def` | Kamus/definisi custom |

---

## 5. Konfigurasi (`static/config.ini`)

```ini
[STATES]
TLS = True            # True = STARTTLS, False = plain TCP
MSERVE = True         # Bot tetap layani meski bukan moderator
GETEXC = True         # Kirim exception detail ke admin
LANG = EN             # Bahasa default (EN/RU/UA/...)

[CLIENT]
SERV = jabber.server.com
PORT = 5222
USER = botusername
HOST = jabber.server.com
PASS = secret

[CONFIG]
RESOURCE = Nexsus
STATUS = Type "HELP" for help with commands
NICK = Nexsus
ADMIN = admin@jabber.server.com    # God-level access (8)

[LIMITS]
MEMORY = 64           # MB, 0 = unlimited
INCOMING = 10240      # Karakter pesan masuk
CHAT = 1024           # Karakter balasan ke room
PRIVATE = 2024        # Karakter balasan ke private chat
CHAT_LIST_LENGTH = 100
```

Multi-account tambahan didaftarkan di `static/clients.ini` dengan format section serupa.

---

## 6. Instalasi & Menjalankan

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Edit konfigurasi
nano static/config.ini

# 3. Jalankan
python3 NexsusBot.py

# Opsional — custom folder:
python3 NexsusBot.py -s static -d current -e expansions
```

Bot akan auto-reconnect setelah crash (delay 30 detik), dan menyimpan PID di `current/sessions.db` untuk mencegah proses duplikat.

---

## 7. Menambah Expansion Baru

Buat folder `expansions/<nama>/code.py`:

```python
# coding: utf-8

class expansion_temp(expansion):

    def __init__(self, name):
        expansion.__init__(self, name)

    AnsBase = ("Pesan jawaban.",)  # index 0, dst

    def command_contoh(self, stype, source, body, disp):
        Answer(self.AnsBase[0], stype, source, disp)

    commands = (
        (command_contoh, "contoh", 1,),  # (handler, nama_command, min_access)
    )
```

Opsional: buat `expansions/<nama>/contoh.en` (file help, format bebas, baris 1-2 = header).

Expansion otomatis termuat saat restart, atau gunakan `expload <nama>` untuk load runtime.

---

## 8. Catatan Migrasi (Python 2 → 3 / xmpppy → slixmpp)

Proyek ini adalah hasil porting dari BlackSmith mark.2 (Python 2, library `xmpppy`). Perubahan utama:

- `xmpppy` → **slixmpp** (asyncio-based)
- `has_key()`, `xrange()`, `itervalues()` → sintaks Python 3
- `itypes.Number()` → `AtomicNumber` (thread-safe counter custom)
- Setiap `NexusClient` berjalan di **asyncio event loop tersendiri** dalam thread daemon
- MUC presence di-parse langsung dari XML (`<x xmlns="muc#user"><item .../></x>`) untuk kompatibilitas penuh dengan slixmpp 1.15.x
