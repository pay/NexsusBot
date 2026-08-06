# Nexsus Serve!

> **Port Python 3 / slixmpp** dari BlackSmith mark.2 (WitcherGeralt)
> Porting Python3 by: paijo.ahmad@jabber.ru

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![slixmpp](https://img.shields.io/badge/XMPP-slixmpp%201.17%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**Versi:** 1.1.0 Core BlackSmith mark.2
**Basis:** Port Python 3 / slixmpp dari BlackSmith mark.2 (WitcherGeralt)
**Protokol:** XMPP (Jabber) — client MUC bot

---

## 1. Ringkasan

Nexsus Serve adalah bot XMPP berbasis arsitektur **expansion** (plugin) — setiap fitur (command, auto-responder, scheduler) adalah modul terpisah yang dimuat otomatis saat startup dari folder `expansions/`. Engine inti (`NexsusBot.py`) menyediakan:

- Koneksi XMPP (multi-account) via **slixmpp**
- Manajemen room MUC (join, roles, affiliations)
- Sistem command dengan prefix dan level akses
- Database SQLite per-fitur
- Sistem help otomatis dari file `.{lang}`
- Asisten AI terintegrasi (Groq) dengan konteks obrolan room
- Watchdog auto-restart dengan grace period, dan self-update dari git via chat command

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
├── config/                    # Konfigurasi rahasia terpisah dari git (secrets)
│   ├── groq_config            # API key Groq (chmod 600, TIDAK di-commit)
│   └── groq_config.example    # Template — aman di-commit, tanpa key asli
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
| `Macro` | Hook global untuk expansion yang intercept command sebagai macro/alias |

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
            └─ Watchdog: restart total kalau SEMUA client putus
               selama >10 menit berturut-turut (grace period,
               supaya tidak restart cuma karena koneksi flaky sesaat)
```

### 3.3 Sistem Akses (Access Level)

| Level | Label | Keterangan |
|---|---|---|
| 8 | God | Admin utama (`ADMIN=` di config.ini), akses penuh — termasuk `update` |
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
  ├─ Macro hook (untuk expansion yang intercept semua pesan, mis. alias)
  └─ Cmds[command].execute() → jalankan handler di thread terpisah
       (kalau bukan command dikenal → diteruskan ke handler "01eh",
        dipakai a.l. oleh expansion 'ai' untuk baca semua chat room)
```

---

## 4. Daftar Expansion (34 Modul)

| Expansion | Command | Fungsi |
|---|---|---|
| `access` | `access`, `acclist`, `acclist2`, `gaccess`, `laccess` | Manajemen access level user |
| `ai` | `ai`, `aiset` | Asisten AI (Groq) — nge-mention bot atau `/ai <tanya>`. Baca konteks 10 pesan terakhir room, simpan history percakapan & log room ke disk |
| `alias` | `alias`, `macro` | Sistem alias/macro custom per-event (join, message, role change, dll) & shortcut command |
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
| `update` | `update` | Cek/tarik update bot dari git (`check`, `pull`, `status`) & restart untuk apply (`restart`). Akses level 8 (God) saja |
| `user_stats` | `userstat`, `here` | Statistik per-user |
| `wtf` | `wtf`, `def` | Kamus/definisi custom |

### 4.1 Expansion `ai` (Groq AI)

- Trigger: mention nick bot di room, atau command `ai <pertanyaan>` (PM/room)
- Provider: **Groq API** (model bisa diganti lewat `aiset model [1-7]`), Ollama sudah dihapus dari arsitektur ini
- **Konteks room**: setiap pesan di room (bukan cuma yang mention bot) direkam ke `.nexsus_ai/room_log.json` (maks 50 pesan/room di disk). Saat AI dipanggil, 10 pesan terakhir disuntik sebagai konteks — supaya jawaban nyambung dengan obrolan berjalan
- History percakapan personal tersimpan terpisah di `.nexsus_ai/history.json`, limit jumlah pesan tersimpan mengikuti access level user
- Command admin: `aiset on|off [global]`, `aiset model`, `aiset ulimit`, `aiset reset all`, `aiset history save|load|info|clear`, `aiset quota`, `aiset ping`, `aiset reloadkey`, `aiset info`
- API key disimpan di `config/groq_config` (lihat §5.1) — **tidak** boleh ikut ter-commit ke git

### 4.2 Expansion `alias`

Porting dari BlackSmith mark.2 (xmpppy) ke Slixmpp. Memungkinkan admin bikin custom trigger berdasarkan event (`message`, `join`, `leave`, `kick`, `ban`, `nick`, `role`, `status`, dll) yang menjalankan command, kirim pesan, atau aksi moderasi otomatis. Juga mendukung `macro` — alias singkat untuk command yang sudah ada.

Catatan: fitur auto-fetch version/capabilities client (XEP-0092/0115) saat user join **tidak** diporting (disederhanakan) — alias event `"join"` tetap jalan tanpa data versi/capabilities.

### 4.3 Expansion `update`

Update bot langsung dari git lewat chat, tanpa perlu masuk terminal:

| Command | Fungsi |
|---|---|
| `update` / `update check` | Cek commit baru di remote (fetch, tanpa narik) |
| `update status` | `git status --short --branch` |
| `update pull` | Tarik update — **otomatis dibatalkan** kalau ada perubahan lokal belum di-commit |
| `update restart` | Restart bot untuk terapkan update yang sudah ditarik |

`update pull` pakai `git pull --ff-only` (tidak akan bikin merge commit otomatis). Karena jalan non-interaktif di background, `git` butuh credential helper tersimpan (`git config --global credential.helper store`) supaya tidak macet minta login.

⚠️ **Catatan keamanan**: siapa pun dengan akses level 8 (God) di bot ini bisa menjalankan `update pull` + `update restart`, yang secara efektif berarti bisa mengganti kode yang dijalankan bot dengan apa pun yang ada di branch remote saat itu. Jaga akses level 8 hanya untuk JID yang benar-benar dipercaya, dan jaga akses tulis ke repo GitHub (branch protection / siapa saja yang punya hak push) sama ketatnya.

---

## 5. Konfigurasi

### 5.1 `static/config.ini`

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

### 5.2 `config/groq_config` (API key untuk expansion `ai`)

```bash
cp config/groq_config.example config/groq_config
chmod 600 config/groq_config
nano config/groq_config   # isi GROQ_API_KEY="key_asli_kamu"
```

Dapatkan API key gratis di [console.groq.com/keys](https://console.groq.com/keys). File `config/groq_config` **sudah masuk `.gitignore`** — jangan pernah paksa-commit file ini, cukup commit `config/groq_config.example` (template tanpa key asli).

---

## 6. Instalasi & Menjalankan

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Edit konfigurasi
nano static/config.ini
cp config/groq_config.example config/groq_config && nano config/groq_config

# 3. Jalankan
python3 NexsusBot.py

# Opsional — custom folder:
python3 NexsusBot.py -s static -d current -e expansions
```

Bot akan auto-reconnect setelah crash (delay 30 detik via `os.execl`), menyimpan PID di `current/sessions.db` untuk mencegah proses duplikat, dan punya watchdog terpisah yang restart total proses kalau **semua** client XMPP putus koneksi selama lebih dari 10 menit berturut-turut (bukan langsung di kegagalan pertama — kasih ruang untuk reconnect logic internal coba dulu).

### 6.1 Auto-start saat boot (Termux)

Contoh `~/.termux/boot/boot.sh`:
```bash
cd ~/xmppbot/nesxusbot && nohup python NexsusBot.py >> nexsus.log 2>&1 & disown
```
Butuh paket `termux-boot` terinstall + app **Termux:Boot** companion, dan `termux-setup-storage` sudah dijalankan sekali kalau mau akses `~/storage/downloads`.

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

Expansion otomatis termuat saat restart, atau gunakan `expload <nama>` untuk load runtime (butuh access level 7+, tergantung config `exp_control`).

---

## 8. Catatan Migrasi (Python 2 → 3 / xmpppy → slixmpp)

Proyek ini adalah hasil porting dari BlackSmith mark.2 (Python 2, library `xmpppy`). Perubahan utama:

- `xmpppy` → **slixmpp** (asyncio-based)
- `has_key()`, `xrange()`, `itervalues()` → sintaks Python 3
- `itypes.Number()` → `AtomicNumber` (thread-safe counter custom)
- Setiap `NexusClient` berjalan di **asyncio event loop tersendiri** dalam thread daemon
- MUC presence di-parse langsung dari XML (`<x xmlns="muc#user"><item .../></x>`) untuk kompatibilitas penuh dengan slixmpp 1.17.x
- `database()` (xmpppy-era alias untuk `itypes.Database`) → class `Database` bawaan NexsusBot
- Expansion `alias`: `xmpp_raise()` (NodeProcessed) dihapus, tidak ada padanan langsung di Slixmpp untuk kasus ini — efek sampingnya minor (redundansi proses non-fatal)
- Handler event `"05eh"` (leave/kick/ban) dan `Macro.__contains__` di core sempat butuh 2 patch tambahan supaya argumen yang dikirim core cocok dengan yang diharapkan expansion `alias` (lihat commit history untuk detail)

---

## 9. Keamanan & Praktik Baik

- **Jangan commit** `config/groq_config`, `.nexsus_ai/history.json`, atau file backup versi (`*.v3`, `*.v4`, dst) — semua sudah masuk `.gitignore` secara default
- Gunakan **Personal Access Token (PAT)**, bukan password akun, untuk `git push`/`pull` via HTTPS — GitHub sudah tidak menerima password biasa sejak 2021
- Akses level 8 (God) setara root — cuma berikan ke JID yang benar-benar dipercaya, terutama karena expansion `update` bisa mengubah kode yang dijalankan bot langsung dari git
- File secret (`config/groq_config`) sebaiknya `chmod 600` — cuma owner yang bisa baca/tulis
