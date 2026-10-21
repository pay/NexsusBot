#!/usr/bin/env python3
# coding: utf-8
"""
make_id_help.py - generate expansions/*/<cmd>.id from expansions/*/<cmd>.en

Help files (plain text, per-language) terpisah dari ans.<lang>.json yang
berisi reply strings. Sebelum tool ini, hanya 4 dari 106 command punya
versi .id, jadi user Indonesia dapat badan help bahasa Inggris.

File .id yang SUDAH ada tidak ditimpa (alias, macro, lang, update).

Jalankan dari root repo:
    python3 tools/make_id_help.py          # generate
    python3 tools/make_id_help.py --check  # report yang belum ada, tanpa tulis
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPS = os.path.join(ROOT, "expansions")

# ── Verba: "bot would show X" -> "bot akan menampilkan X" ────────────
VERB = {
    "show": "menampilkan", "set": "mengatur", "add": "menambahkan",
    "remove": "menghapus", "delete": "menghapus", "list": "menampilkan daftar",
    "enable": "mengaktifkan", "disable": "menonaktifkan", "give": "memberi",
    "take": "mengambil", "send": "mengirim", "make": "membuat",
    "write": "menulis", "read": "membaca", "create": "membuat",
    "clear": "menghapus", "reset": "mengatur ulang", "check": "memeriksa",
    "print": "mencetak", "display": "menampilkan",
}

# ── Tail unik: kalimat pendek setelah verba ───────────────────────────
TAIL = {
    '"AAA!!" in to admin\'s jid': '"AAA!!" ke JID admin',
    '"AAA!!" in to all chats as: [Message from <your nick/resource>:][new line][AAA!!]':
        '"AAA!!" ke semua chat sebagai: [Pesan dari <nick/resource kamu>:][baris baru][AAA!!]',
    '"AAA!!" to chel@jabber.com as: [Message from <your nick/resource>:][new line][AAA!!]':
        '"AAA!!" ke chel@jabber.com sebagai: [Pesan dari <nick/resource kamu>:][baris baru][AAA!!]',
    '"Aaa!!" in to Superadmin\'s JID': '"Aaa!!" ke JID Superadmin',
    '"apple" from the global base (access 7)': '"apple" dari base global (access 7)',
    '"apple" to the global base (access 7)': '"apple" ke base global (access 7)',
    '"google" from the base of conference': '"google" dari base conference',
    '"google" to the base of conference': '"google" ke base conference',
    '"qwerty@xmpp.ru" from the roster': '"qwerty@xmpp.ru" dari roster',
    '"qwerty@xmpp.ru" in to the group "Admins" with nick "Qwerty"':
        '"qwerty@xmpp.ru" ke grup "Admins" dengan nick "Qwerty"',
    '"qwerty@xmpp.ru" in to the group "Users"': '"qwerty@xmpp.ru" ke grup "Users"',
    '"some_server.com" from "white list"': '"some_server.com" dari "white list"',
    '"white list" of servers': '"white list" server',
    '(unix) how much memory use prosess with pid 12154':
        '(unix) berapa memori yang dipakai proses dengan pid 12154',
    '(windows) python task list & used ram': '(windows) daftar task python & ram terpakai',
    '1st search result': 'hasil pencarian pertama',
    "Dude's access": 'access Dude',
    "Dude's idle (if client allow that)": 'idle Dude (kalau client mengizinkan)',
    "Dude's ping": 'ping Dude',
    "Dude's statistic in current conference": 'statistik Dude di conference ini',
    "Dude's statistics": 'statistik Dude',
    "Dude's vCard": 'vCard Dude',
    'IMDb Top 250 Movies': 'IMDb Top 250 Film',
    'PID.txt and show it\'s content': 'PID.txt beserta isinya',
    'a quote with number 30456': 'kutipan nomor 30456',
    'a random quote': 'kutipan acak',
    'access level 6 for Obi-Wan Kenobi': 'access level 6 untuk Obi-Wan Kenobi',
    'all names of the definitions': 'semua nama definisi',
    'all of the visitors': 'semua pengunjung',
    'all of the visitors, who joined today': 'semua pengunjung yang join hari ini',
    'all of the visitors, with dates of join': 'semua pengunjung beserta tanggal join',
    'all of the visitors, with their roles on exit': 'semua pengunjung beserta role saat keluar',
    'all of your notes': 'semua catatan kamu',
    'all scheduled tasks': 'semua task terjadwal',
    'all your records from notepade': 'semua catatanmu dari notepade',
    'away dude\'s affiliation': 'affiliation Away',
    'calendar for current month': 'kalender untuk bulan ini',
    'calendar for may of this year': 'kalender untuk Mei tahun ini',
    'calendar for the 1st month of the 1st millennium':
        'kalender untuk bulan pertama milenium pertama',
    'client with jid bs@xmpp.ru, and when will rejoin rooms behind which establishes this jid from another':
        'client dengan jid bs@xmpp.ru, dan kapan akan join ulang room yang ditangani jid ini dari client lain',
    "client's version of Dude": 'versi client Dude',
    "client's version of dude@jabr.com": 'versi client dude@jabr.com',
    'command "talkers"': 'command "talkers"',
    'command prefix - "!"': 'prefix command - "!"',
    'conference subject - "Hello everybody!"': 'subject conference - "Halo semua!"',
    "converter's categorys": 'kategori converter',
    'current config': 'config saat ini',
    'current password': 'password saat ini',
    'current prefix': 'prefix saat ini',
    'definition of "bot" (if it exists in the bases)': 'definisi "bot" (kalau ada di base)',
    'definitions count': 'jumlah definisi',
    'dude a participant': 'dude sebagai participant',
    'dude a visitor': 'dude sebagai visitor',
    'dude admin of the conference': 'dude sebagai admin conference',
    'dude member of the conference': 'dude sebagai member conference',
    'dude moderator of the conference': 'dude sebagai moderator conference',
    'dude owner of the conference': 'dude sebagai owner conference',
    "dude's statistics": 'statistik dude',
    'exception with number one': 'exception nomor satu',
    'expansions list': 'daftar expansion',
    'how much time dude spent in conference': 'berapa lama dude berada di conference',
    'how much time you spent in conference': 'berapa lama kamu berada di conference',
    'implemented programming/scripting/marking languages':
        'bahasa pemrograman/scripting/marking yang didukung',
    'info about command "join"': 'info tentang command "join"',
    'info about command "join" on russian': 'info tentang command "join" dalam bahasa Rusia',
    'info. about expansion "help"': 'info tentang expansion "help"',
    'invite to someone@jabber.ru': 'undangan ke someone@jabber.ru',
    'list of the chats to the user with nickname "Mister Anonymous"':
        'daftar chat untuk user dengan nick "Mister Anonymous"',
    'local access with level 6 for Obi-Wan Kenobi':
        'access lokal dengan level 6 untuk Obi-Wan Kenobi',
    'new note': 'catatan baru',
    'next result': 'hasil berikutnya',
    'next translation': 'terjemahan berikutnya',
    'note from line 7': 'catatan dari baris 7',
    'note in line 13': 'catatan di baris 13',
    'number of unexpected exceptions': 'jumlah exception tak terduga',
    'obi-wan_kenobi@jab.net from global access list':
        'obi-wan_kenobi@jab.net dari daftar access global',
    'obi-wan_kenobi@jab.net from local access list':
        'obi-wan_kenobi@jab.net dari daftar access lokal',
    'password "codename" to his join config of current chatroom':
        'password "codename" ke config join chatroom ini',
    'password from his join config': 'password dari config join-nya',
    'pong-time to private': 'waktu pong ke private',
    'prefix': 'prefix',
    'rating of current chatroom': 'rating chatroom ini',
    'roster access state': 'status access roster',
    'rules': 'aturan',
    'satus "xa" with text "I\'m far far away" in current conference':
        'status "xa" dengan teks "I\'m far far away" di conference ini',
    'satus in all chats where he sets': 'status di semua chat tempat dia aktif',
    'satus in some_chat@c.j.ru': 'status di some_chat@c.j.ru',
    'shortlist of the visitors': 'daftar ringkas pengunjung',
    'statistic of dude@jub.net in all of the conferences where bot serves':
        'statistik dude@jub.net di semua conference yang dilayani bot',
    'statistics of command "help"': 'statistik command "help"',
    "statistics of it's current jid's server": 'statistik server JID bot saat ini',
    'statistics of jabr.com': 'statistik jabr.com',
    'statistics of top 20 commands': 'statistik 20 command teratas',
    "support's rating": 'rating support',
    'supported languages': 'bahasa yang didukung',
    'talkers top of all of the conferences where bot serves':
        'top pembicara dari semua conference yang dilayani bot',
    'talkers top of current conference': 'top pembicara dari conference ini',
    'the 1st 25 of IMDb Top 250 Movies': '25 pertama dari IMDb Top 250 Film',
    "the enumerated list of it's roster users": 'daftar nomor dari user roster-nya',
    'the idle of dude@jabr.com': 'idle dari dude@jabr.com',
    "the list of conference's owners": 'daftar owner conference',
    'the list of disabled commands': 'daftar command yang dinonaktifkan',
    'the list of forbidden commands': 'daftar command terlarang',
    'the list of online users of example@conference.jabber.ru':
        'daftar user online di example@conference.jabber.ru',
    'the list of services of jabber.ru': 'daftar service di jabber.ru',
    'the page of the movie with id 530 (A Beautiful Mind)':
        'halaman film dengan id 530 (A Beautiful Mind)',
    'the ping of dude@jabr.com': 'ping dari dude@jabr.com',
    'the state of command "talkers"': 'status command "talkers"',
    'the statistics of dude@jabr.com': 'statistik dari dude@jabr.com',
    'the time of Dude': 'waktu aktif Dude',
    'the time of dude@jabr.com': 'waktu aktif dude@jabr.com',
    'top 100 talkers of all of the conferences where bot serves':
        '100 pembicara teratas dari semua conference yang dilayani bot',
    'top 20 conferences with max users of jabber.ru':
        '20 conference dengan user terbanyak di jabber.ru',
    'top 50 talkers of current conference': '50 pembicara teratas dari conference ini',
    'units from category "temperature"': 'satuan dari kategori "temperature"',
    "uptime of it's current jid's server": 'uptime server JID bot saat ini',
    'uptime of jabr.com': 'uptime jabr.com',
    'vCard of dude@jabr.com': 'vCard dari dude@jabr.com',
    'your access': 'access kamu',
    "your client's version": 'versi client kamu',
    'your ping': 'ping kamu',
    'your statistic in all of the conferences where bot serves':
        'statistik kamu di semua conference yang dilayani bot',
    'your statistic in current conference': 'statistik kamu di conference ini',
    'your statistics': 'statistik kamu',
    'your time': 'waktu aktif kamu',
    'your vCard': 'vCard kamu',
}

# ── Penjelasan yang BUKAN "bot would ..." ─────────────────────────────
EXPL = {
    "Macro names are registered as real commands - just type the macro's name like any command.":
        "Nama macro didaftarkan sebagai command sungguhan - tinggal ketik nama macronya seperti command biasa.",
    "Needs access level 8 (God). Git must already have stored credentials (git config --global credential.helper store) or 'pull' will stall asking for a login.":
        "Butuh access level 8 (God). Git harus sudah menyimpan kredensial (git config --global credential.helper store) atau 'pull' akan berhenti minta login.",
    "Notes:": "Catatan:",
    "Put 'global' in front to manage aliases that apply in every room (access 7). Without it you only manage aliases for this room. See also: help macro":
        "Taruh 'global' di depan untuk mengelola alias yang berlaku di semua room (access 7). Tanpa itu, kamu hanya mengelola alias untuk room ini. Lihat juga: help macro",
    'activation of "Sparta mode" (bot will ban all of new servers which are not in "white list")':
        'aktivasi "Sparta mode" (bot akan ban semua server baru yang tidak ada di "white list")',
    "activation of antiwipe feature": "aktivasi fitur antiwipe",
    "activation of protection service from advertisement":
        "aktivasi proteksi dari advertisement",
    "aiset subcommands (access level 1 for basic, 3 for admin):":
        "subcommand aiset (access level 1 untuk dasar, 3 untuk admin):",
    "answer would be -> ['1', '2', '1', '2', '1', '2']":
        "jawabannya -> ['1', '2', '1', '2', '1', '2']",
    'bot informs that the command "join" is located in to "basic_control" expansion':
        'bot memberi tahu bahwa command "join" ada di expansion "basic_control"',
    'bot informs that the command "join" requires access 7':
        'bot memberi tahu bahwa command "join" butuh access 7',
    'bot wiil set "Bot control center" as default resource and RAM usage limit - 96mb':
        'bot akan set "Bot control center" sebagai resource default dan limit RAM - 96mb',
    "deactivation of authorisation feature": "deaktivasi fitur otorisasi",
    "deactivation of protection service from caps-flood":
        "deaktivasi proteksi dari caps-flood",
    "deactivation of protection service from obscene":
        "deaktivasi proteksi dari obscene",
    "executes the command in the room from the list at number 1, and report the results in to this conference":
        "menjalankan command di room dari daftar nomor 1, dan melaporkan hasilnya ke conference ini",
    'executes the command like as would you set it while in "witcher@conference.jabber.ru", and send the results to you in private':
        'menjalankan command seperti yang kamu jalankan di "witcher@conference.jabber.ru", lalu mengirim hasilnya ke kamu secara private',
    "lang_from would detected automatically": "lang_from terdeteksi otomatis",
    "level of user access to which will respond to the security services (from 1 to 5)":
        "level access user yang dilayani security service (dari 1 sampai 5)",
    "maximum length of status messages, to allow for users (from 128 to 512)":
        "panjang maksimal pesan status untuk user (dari 128 sampai 512)",
    "maximum message length allowed for users (from 512 to 2048)":
        "panjang maksimal pesan yang diizinkan untuk user (dari 512 sampai 2048)",
    "number of kick after that will ban follow (from 2 to 6)":
        "jumlah kick sebelum ban berikutnya (dari 2 sampai 6)",
    "set the maximum length nickname for users (from 12 to 32)":
        "set panjang maksimal nick untuk user (dari 12 sampai 32)",
    "shows ordered list of the chatrooms": "menampilkan daftar chatroom terurut",
    "spaces at the edges of nicks will be forbidden":
        "spasi di awal/akhir nick akan dilarang",
    "the <lang> tag on your client's presence is the automatic default a manual pick sticks until you run {command} auto":
        "tag <lang> di presence client kamu adalah default otomatis; pilihan manual bertahan sampai kamu jalankan {command} auto",
    "time (in seconds) for which user will be deprived of voting for violations (60 to 360)":
        "waktu (dalam detik) user kehilangan hak suara karena pelanggaran (60 sampai 360)",
}

# ── Deskripsi: baris pertama tiap file ───────────────────────────────
DESC = {
    "bot shows your accecs or access of specified user":
        "bot menampilkan access kamu atau access user tertentu",
    "bot shows access table": "bot menampilkan tabel access",
    "bot shows local access table": "bot menampilkan tabel access lokal",
    "bot sets global access": "bot mengatur access global",
    "bot sets local access": "bot mengatur access lokal",
    "quotes from bash.org": "kutipan dari bash.org",
    'Chuck Norris "Facts" from chucknorrisfacts.com':
        '"Fakta" Chuck Norris dari chucknorrisfacts.com',
    "file downloader": "pengunduh file",
    "google search": "pencarian google",
    "info about movies (imdb.com)": "info tentang film (imdb.com)",
    "chat's rating from jc.jabber.ru": "rating chat dari jc.jabber.ru",
    "uploading to the Ubuntu Pastebin (paste.ubuntu.com)":
        "upload ke Ubuntu Pastebin (paste.ubuntu.com)",
    "news from python.org": "berita dari python.org",
    "url shortener (powered by is.gd)": "pemendek URL (powered by is.gd)",
    "google translate": "google translate",
    'checking bot "liveliness"': 'cek "kehidupan" bot',
    "default calendar (python's lib. calendar.month)":
        "kalender bawaan (python's lib. calendar.month)",
    "control of the prohibition on the commands in the conference":
        "pengaturan larangan command di conference",
    "clients control system": "sistem kontrol client",
    "config control system (changes will be apply after restart)":
        "sistem kontrol config (perubahan berlaku setelah restart)",
    "converter": "konverter",
    "scheduler (all times are in UTC)": "penjadwal (semua waktu dalam UTC)",
    "Domain Name System": "Domain Name System",
    "checks for the opened port": "cek port yang terbuka",
    "info. about bot's expansions": "info tentang expansion bot",
    "expansions loader (reloader)": "loader expansion (reloader)",
    "expansions and functions unloader": "unloader expansion dan function",
    "controller of the commands": "pengatur command",
    "executes the specified command and sends answer to private":
        "menjalankan command tertentu dan mengirim jawaban ke private",
    "redirecting of a command's executing result to an another user (into private)":
        "mengalihkan hasil eksekusi command ke user lain (ke private)",
    "executes the specified command remotely": "menjalankan command tertentu secara remote",
    "executes sequence of 2-4 commands (users with access more than 7 can use more than 4 commands)":
        "menjalankan urutan 2-4 command (user dengan access di atas 7 bisa pakai lebih dari 4 command)",
    'Game "Rock-paper-scissors-lizard-Spock" from the sitcom "The Big Bang Theory"':
        'Game "Rock-paper-scissors-lizard-Spock" dari sitcom "The Big Bang Theory"',
    "xmpp disco": "xmpp disco",
    "users's idle": "idle user",
    "affiliation lists": "daftar affiliation",
    "xmpp ping": "xmpp ping",
    "xmpp ping statistics": "statistik xmpp ping",
    "statistics of jabber servers": "statistik server jabber",
    "shows local time of the user": "menampilkan waktu lokal user",
    "servers's uptime": "uptime server",
    "xmpp vCard": "xmpp vCard",
    "xmpp version": "xmpp version",
    "calculator": "kalkulator",
    "calculates python's code": "menghitung kode python",
    "executes python's code": "menjalankan kode python",
    "executes shell command": "menjalankan command shell",
    "change which language the bot replies in - for you only, in this room only":
        "ganti bahasa balasan bot - hanya untuk kamu, hanya di room ini",
    "gives admin rights": "memberi hak admin",
    "add to outcast": "tambahkan ke outcast",
    "global add to outcast": "tambah global ke outcast",
    "global unban (take away affiliation)": "unban global (hapus affiliation)",
    "kick some user": "kick user",
    "gives regular participant rights": "memberi hak participant biasa",
    "gives moderator rights": "memberi hak moderator",
    "take away affiliation (unban)": "hapus affiliation (unban)",
    "gives owner rights": "memberi hak owner",
    "gives participant role": "memberi role participant",
    "set subject": "set subject",
    "take away the voice": "hapus voice",
    "shows how much is left until the new year (UTC)":
        "menampilkan sisa waktu menuju tahun baru (UTC)",
    "your personal notepade with 16 lines": "notepade pribadi kamu berisi 16 baris",
    "roster controller": "pengatur roster",
    "roster access controller": "pengatur access roster",
    "replacement of the jid from which the bot will serve the specific conference":
        "ganti JID dari mana bot melayani conference tertentu",
    "bot's nick changing": "ganti nick bot",
    "sets bot's chatrom's status": "set status chatroom bot",
    "shows/sets bot's chat's password config": "tampilkan/set config password chat bot",
    "shows/sets (for owners only) command prefix (list: !, @ , #, ., *)":
        "tampilkan/set (khusus owner) prefix command (daftar: !, @ , #, ., *)",
    "bot's uptime": "uptime bot",
    "statistics of the commands": "statistik command",
    "exceptions cache": "cache exception",
    "statistics of the bot": "statistik bot",
    "security control system": "sistem kontrol keamanan",
    "statistic of talkers": "statistik pembicara",
    "bot translate text's layout (EN <-> RU)":
        "bot terjemahkan layout teks (EN <-> RU)",
    "time specified user spent in the conference":
        "waktu yang dihabiskan user tertentu di conference",
    "conferense users statistics": "statistik user conference",
    "control of wtf-bases": "pengatur wtf-base",
    "shows wtf-base content": "menampilkan isi wtf-base",
}

# usage (baris kedua) biasanya cuma placeholder -> biarkan apa adanya
# tapi beberapa perlu penjelasan singkat; pakai dict kalau ada.
USAGE = {}


DESC.update({
    "bot joins specified chatroom": "bot join ke chatroom tertentu",
    "bot leaves the conference": "bot keluar dari conference",
    "bot rejoins chatroom": "bot join ulang ke chatroom",
    "bot reloads": "bot reload",
    "bot searchs users in it's lists": "bot mencari user di daftarnya",
    "bot sends 24 messages without <body>, it makes chatroom clean":
        "bot kirim 24 pesan tanpa <body>, supaya chatroom bersih",
    "bot sends invite for specified user": "bot kirim undangan untuk user tertentu",
    "bot sends message in to all chats that he serving":
        "bot kirim pesan ke semua chat yang dilayani",
    "bot sends message in to current chat": "bot kirim pesan ke chat saat ini",
    "bot sends message in to jid of main admin": "bot kirim pesan ke JID admin utama",
    "bot sends message in to specified jid": "bot kirim pesan ke JID tertentu",
    "bot sends the rest of bot's last long message":
        "bot kirim sisa pesan panjang terakhirnya",
    "bot shows a list of it's conferences": "bot menampilkan daftar conference-nya",
    "bot shows a list of users which presences in the conference":
        "bot menampilkan daftar user yang ada di conference",
    "bot shows command's location": "bot menampilkan lokasi command",
    "bot shows full command list": "bot menampilkan daftar lengkap command",
    "bot shows help": "bot menampilkan bantuan",
    "bot shows how much access requires a specified command":
        "bot menampilkan access yang dibutuhkan sebuah command",
    "bot shows info about connection of it's jids":
        "bot menampilkan info koneksi JID-nya",
    "bot shows the visitors of the conference": "bot menampilkan pengunjung conference",
    "bot's clients reconnect functoin": "fungsi reconnect client bot",
    "bot's shutdown": "shutdown bot",
})

EXPL.update({
    "bot would 'ping' you and three users": "bot akan 'ping' kamu dan tiga user lain",
    'bot would allow command "bash" (if it is forbidden, of course)':
        'bot akan mengizinkan command "bash" (kecuali yang memang dilarang)',
    'bot would append "some_server.com" to "white list"':
        'bot akan menambahkan "some_server.com" ke "white list"',
    "bot would ban dude globally": "bot akan ban dude secara global",
    "bot would ban manbearpig": "bot akan ban manbearpig",
    "bot would ban manbearpig with reason that confirms Al Gore was right - Excelsior!":
        "bot akan ban manbearpig dengan alasan yang membuktikan Al Gore benar - Excelsior!",
    "bot would block access to the roster (access free just for bot's admins)":
        "bot akan blok akses ke roster (gratis hanya untuk admin bot)",
    'bot would change his nick to "botik"': 'bot akan ganti nick-nya jadi "botik"',
    "bot would change jid's password (password specify is optional, bot can generate it. with parameter \"set\" after password, bot will just write it)":
        'bot akan ganti password JID (password opsional, bot bisa generate sendiri. dengan parameter "set" setelah password, bot hanya menuliskannya)',
    "bot would clean the conference on the 27th of current month at 21:00 (UTC)":
        "bot akan bersihkan conference tanggal 27 bulan ini jam 21:00 (UTC)",
    "bot would convert 3 miles to metres (4828)": "bot akan konversi 3 mil ke meter (4828)",
    "bot would download Black-2.30.r71.zip (for superadmins loads into bot's root folder)":
        "bot akan unduh Black-2.30.r71.zip (untuk superadmin, ditaruh di folder root bot)",
    "bot would execute 'test' 4 times with a timeout in 6 minutes":
        "bot akan jalankan 'test' 4 kali dengan timeout 6 menit",
    'bot would execute an expression and try to return variable "result"':
        'bot akan jalankan ekspresi dan coba mengembalikan variabel "result"',
    "bot would execute an expression using local namespace":
        "bot akan jalankan ekspresi memakai namespace lokal",
    'bot would execute an expression using local namespace and return "result"':
        'bot akan jalankan ekspresi memakai namespace lokal dan mengembalikan "result"',
    "bot would execute an expression without notice about the completion":
        "bot akan jalankan ekspresi tanpa pemberitahuan selesai",
    'bot would forbid command "bash"': 'bot akan melarang command "bash"',
    "bot would inform you how to use it": "bot akan memberi tahu cara pakainya",
    "bot would join chat@conference.jab.com": "bot akan join chat@conference.jab.com",
    'bot would join chatroom with "loko-champ" as the chatroom password and set command prefix - "!"':
        'bot akan join chatroom dengan password "loko-champ" dan set prefix command - "!"',
    "bot would join chatroom with nick \"Black-Bot\" and jid \"bot@j.ru\" (if it is bot's jid)":
        'bot akan join chatroom dengan nick "Black-Bot" dan jid "bot@j.ru" (kalau itu JID bot)',
    "bot would kick dude": "bot akan kick dude",
    "bot would leave current chatroom": "bot akan keluar dari chatroom ini",
    "bot would leave some_chat@conference.jabber.ru (if he is there)":
        "bot akan keluar dari some_chat@conference.jabber.ru (kalau dia ada di sana)",
    'bot would load expansion "help"': 'bot akan load expansion "help"',
    "bot would open access to the roster (access free just for all users)":
        "bot akan buka akses ke roster (gratis untuk semua user)",
    'bot would ping "Some_User" after 60 seconds':
        'bot akan ping "Some_User" setelah 60 detik',
    "bot would ping you on 2nd December at 18:40:20 (UTC)":
        "bot akan ping kamu tanggal 2 Desember jam 18:40:20 (UTC)",
    "bot would play the game with you": "bot akan main game dengan kamu",
    'bot would put file into "Downloads" with name "Black-2.zip"':
        'bot akan taruh file di "Downloads" dengan nama "Black-2.zip"',
    'bot would put file into "Zip" (only for superadmins, otherwise loads into "Downloads")':
        'bot akan taruh file di "Zip" (hanya superadmin, selain itu ke "Downloads")',
    "bot would reconnect bot@jabber.ru": "bot akan reconnect bot@jabber.ru",
    "bot would reconnect current jid": "bot akan reconnect JID saat ini",
    "bot would rejoin current chatroom": "bot akan join ulang ke chatroom ini",
    "bot would rejoin some_chat@conference.jabber.ru (if he is there)":
        "bot akan join ulang some_chat@conference.jabber.ru (kalau dia ada di sana)",
    "bot would reload": "bot akan reload",
    "bot would reload silently": "bot akan reload tanpa suara",
    'bot would reload with status "diagnostics"': 'bot akan reload dengan status "diagnostics"',
    "bot would replace his current jid in chat@conference.jab.com to some_name@jab.com":
        "bot akan ganti JID-nya di chat@conference.jab.com jadi some_name@jab.com",
    "bot would replace his current jid in currebt chatroom to some_name@jab.com":
        "bot akan ganti JID-nya di chatroom ini jadi some_name@jab.com",
    'bot would search "dude" in chat\'s affiliation lists':
        'bot akan cari "dude" di daftar affiliation chat',
    'bot would search "porn" in the bases': 'bot akan cari "porn" di base',
    'bot would search "witcher" on conference.jabber.ru & show up to 10 results (max 24 results in chat, max 256 in private, 16 default)':
        'bot akan cari "witcher" di conference.jabber.ru & tampilkan sampai 10 hasil (maks 24 hasil di chat, maks 256 di private, default 16)',
    "bot would search Masha and tell you where is she":
        "bot akan cari Masha dan memberi tahu di mana dia",
    'bot would search a movie with name "2012"': 'bot akan cari film dengan nama "2012"',
    'bot would search a movie with name "A Beautiful Mind"':
        'bot akan cari film dengan nama "A Beautiful Mind"',
    'bot would send: "AAA!!"': 'bot akan kirim: "AAA!!"',
    "bot would shorten url to http://is.gd/FntYVl": "bot akan memendekkan URL jadi http://is.gd/FntYVl",
    "bot would shutdown": "bot akan shutdown",
    "bot would shutdown silently": "bot akan shutdown tanpa suara",
    'bot would shutdown with status "update"': 'bot akan shutdown dengan status "update"',
    "bot would start client with jid bs@xmpp.ru (if host=server, server specify is optional, such as a port if it=5222)":
        "bot akan mulai client dengan jid bs@xmpp.ru (kalau host=server, nama server opsional, misalnya port kalau port=5222)",
    "bot would stop the task with ID=47": "bot akan menghentikan task dengan ID=47",
    'bot would translate "hello world" to russian': 'bot akan terjemahkan "hello world" ke bahasa Rusia',
    "bot would translate this text": "bot akan terjemahkan teks ini",
    "bot would translate your last post": "bot akan terjemahkan post terakhirmu",
    "bot would turn on command": "bot akan menyalakan command",
    "bot would unban dude globally": "bot akan unban dude secara global",
    'bot would unload expansion "talkers"': 'bot akan unload expansion "talkers"',
    "bot would unload talkers calculator (unloader should use only users with experience)":
        "bot akan unload kalkulator talkers (unloader sebaiknya cuma untuk user berpengalaman)",
    "bot would upload a text as Javascript source code and return link to it":
        "bot akan upload teks sebagai kode sumber Javascript dan mengembalikan link-nya",
    "bot would upload a text as Python Traceback and return link to it":
        "bot akan upload teks sebagai Python Traceback dan mengembalikan link-nya",
    "bot would upload a text just as plain text":
        "bot akan upload teks apa adanya sebagai teks biasa",
})

def parse(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip() for l in fh.read().split("\n")]
    while lines and not lines[-1].strip():
        lines.pop()
    desc = lines[0].strip() if lines else ""
    usage = lines[1].strip() if len(lines) > 1 else ""
    pairs = []
    i = 2
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("*/"):
            rest = line[2:].strip()
            j = i + 1
            body = []
            while j < len(lines) and not lines[j].strip().startswith("*/"):
                if lines[j].strip():
                    body.append(lines[j].strip())
                j += 1
            pairs.append((rest, " ".join(body)))
            i = j
        else:
            i += 1
    return desc, usage, pairs


def tr_expl(text):
    """Terjemahkan penjelasan satu baris."""
    if not text:
        return text
    if text in EXPL:
        return EXPL[text]
    m = re.match(r"^bot would (\w+)\s+(.*)$", text)
    if m:
        verb, tail = m.group(1), m.group(2)
        if verb in VERB and tail in TAIL:
            return "bot akan %s %s" % (VERB[verb], TAIL[tail])
    return None  # tidak bisa


def tr_desc(text):
    if text in DESC:
        return DESC[text]
    if text.startswith("{command}"):
        return text  # placeholder syntax, biarkan
    return None


def main():
    check = "--check" in sys.argv
    made = []
    missing = []
    for exp in sorted(os.listdir(EXPS)):
        edir = os.path.join(EXPS, exp)
        if not os.path.isdir(edir):
            continue
        for fn in sorted(os.listdir(edir)):
            if not fn.endswith(".en") or fn == "name.en":
                continue
            stem = fn[:-3]
            en_path = os.path.join(edir, fn)
            id_path = os.path.join(edir, stem + ".id")
            if os.path.isfile(id_path):
                continue
            desc, usage, pairs = parse(en_path)
            d = tr_desc(desc)
            if d is None:
                missing.append((exp, stem, "desc: " + desc[:60]))
                continue
            out = [d, usage]
            bad = False
            for cmd, expl in pairs:
                e = tr_expl(expl)
                if e is None:
                    bad = True
                    break
                out.append("*/" + cmd)
                out.append(e)
            if bad:
                missing.append((exp, stem, "expl"))
                continue
            if not check:
                with open(id_path, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(out) + "\n")
            made.append((exp, stem))
    if check:
        print("belum bisa: %d" % len(missing))
        for m in missing:
            print("  %s/%s  %s" % m)
    else:
        print("dibuat: %d file .id" % len(made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
