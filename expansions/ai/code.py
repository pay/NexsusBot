# coding: utf-8
# Plugin: ai
# Author: paijo.ahmad@jabber.ru
# NexsusBot Expansion — Groq AI (Ollama dihapus)
# exp_name = "ai" # /code.py v.8.2 (+ room log & context)

import urllib.request
import urllib.error
import json
import threading
import os as _os
import re

# ── Groq config ──────────────────────────────────────────────
GROQ_API_BASE    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_CONFIG_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(ExpsDir)), "config", "groq_config")
GROQ_MODELS = {
    "1": ("openai/gpt-oss-120b",                              "GPT-OSS 120B"),
    "2": ("meta-llama/llama-4-scout-17b-16e-instruct",        "Llama 4 Scout"),
    "3": ("llama-3.3-70b-versatile",                          "Llama 3.3 70B"),
    "4": ("qwen/qwen3-32b",                                   "Qwen3 32B"),
    "5": ("qwen/qwen3.6-27b",                                 "Qwen3.6 27B"),
    "6": ("openai/gpt-oss-20b",                               "GPT-OSS 20B"),
    "7": ("llama-3.1-8b-instant",                             "Llama 3.1 8B"),
}
GROQ_MODEL_DEFAULT = "1"

TIMEOUT    = 60
CHUNK_SIZE = 800   # fix: dinaikkan dari 400

# ── Persistensi ──────────────────────────────────────────────
HISTORY_DIR            = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".nexsus_ai")
HISTORY_FILE           = _os.path.join(HISTORY_DIR, "history.json")
ULIMIT_FILE            = _os.path.join(HISTORY_DIR, "ulimit.json")
HISTORY_MAX_AGE        = 7
HISTORY_FLUSH_INTERVAL = 300

# ── Room log (rekam semua posting room + konteks ke AI) ──────
ROOM_LOG_FILE   = _os.path.join(HISTORY_DIR, "room_log.json")
ROOM_LOG_MAX    = 50    # jumlah pesan mentah disimpan per-room di disk
ROOM_CTX_LIMIT  = 10    # jumlah pesan terakhir yang disuntik sebagai konteks ke AI
ROOM_MSG_MAXLEN = 300   # potong pesan mentah yang kepanjangan sebelum disimpan

AI_VERSION  = "v8.2"
WAITING_MSG = "mohon tunggu... (nexsus:%s)"

HISTORY_BY_ACCESS = (
    (8, 9999),
    (7, 90),
    (5, 70),
    (3, 50),
    (1, 30),
    (0, 0),
)

SYSTEM_PROMPT = (
    "Kamu adalah teman ngobrol di grup chat XMPP -- bukan asisten kaku, tapi "
    "temen yang ramah, agak jahil, dan suka ngeledekin dengan gemas (bukan "
    "menghina beneran). Boleh sarkas dikit, boleh nyeletuk, boleh balas becanda "
    "kalau diajak becanda -- tapi tetap sayang sama semua orang di grup, bukan "
    "toxic. Jawab dalam bahasa yang sama dengan bahasa pesan user -- kalau "
    "user bahasa Indonesia, jawab bahasa Indonesia; kalau user bahasa "
    "Inggris, jawab bahasa Inggris; kalau user bahasa Arab, jawab bahasa "
    "Arab, dst. Gaya bicara santai, singkat, dan to the point, maksimal "
    "sekitar 10-15 baris. Pakai emoji secukupnya yang sesuai sama emosi/nada "
    "obrolan (jangan spam emoji, cukup 1-3 per pesan kalau memang pas)."
    "\n\n"
    "Kalau ditanya serius (info, bantuan, pertanyaan faktual), tetap jawab "
    "dengan benar dan jujur -- jahilnya taruh di gaya bicara, bukan di isi "
    "jawaban. Kalau tidak tahu jawabannya, ngaku terus terang tidak tahu, "
    "jangan mengarang, boleh dibungkus becanda tapi jangan sampai menyesatkan.\n\n"
    "Pesan dari anggota grup dikirim dengan format [nama]: isi pesan. Nama di "
    "dalam kurung siku itu adalah orang yang sedang bicara -- pakai nama itu "
    "kalau menyapa/ngeledekin balik, jangan pakai nama bot sendiri. Kadang kamu "
    "juga akan diberi cuplikan obrolan room sebelumnya sebagai konteks -- pakai "
    "itu buat nyambung, tapi jangan membalas cuplikan itu satu-satu, cukup "
    "tanggapi pesan terbaru. Jawab LANGSUNG isi jawaban tanpa label pembicara apa pun di depan -- jangan pernah memulai jawaban dengan '[nama]:' atau 'nama:', karena bot sudah otomatis mencantumkan nama pembicara di depan pesan yang dikirim ke room.\n\n"
    "Ledekan/sarkasme HANYA buat suasana becanda ringan -- jangan pernah "
    "menghina fisik, SARA, atau hal yang bisa beneran nyakitin orang. Kalau ada "
    "yang kelihatan tersinggung beneran (bukan lagi ikut becanda), langsung "
    "turunkan nada, minta maaf santai, dan jangan diterusin ngeledekinnya. "
    "Kalau ada pelanggaran serius (menghina serius, spam, SARA provokatif, "
    "konten ilegal/NSFW), tegur dengan tegas tapi tetap sopan -- ini bukan "
    "waktunya jahil. Kalau ada yang bertengkar beneran, ajak semua tenang dan "
    "saling menghormati. Kamu cuma mengingatkan, bukan admin -- biarkan manusia "
    "yang menindak lebih lanjut kalau perlu.\n\n"
    "Kamu bisa diajak ngobrol topik apa saja, termasuk bantu soal pemrograman "
    "(termasuk Python) kalau ditanya serius -- pas jawab teknis, jahilnya "
    "dikurangin, jawab kodenya langsung dan benar, kalau ada bug jelaskan "
    "singkat penyebabnya lalu kasih perbaikannya."
)


# ── Load Groq API key ────────────────────────────────────────
def _load_groq_key():
    try:
        with open(GROQ_CONFIG_FILE) as f:
            for line in f:
                if line.startswith("GROQ_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


class expansion_temp(expansion):
    name = "ai"

    AnsBase = (
        "AI is currently disabled.",                                          # 0
        "Your conversation history has been deleted.",                        # 1
        "[Nexsus] AI is ready! (%s)\n"                                        # 2
        "Provider: %s\n"
        "History : %d/%s messages\n"
        "Use     : ai <question>\n"
        "Reset   : ai reset",
        "[Nexsus] %s",                                                        # 3
        "AI %s (global).",                                                    # 4
        "AI is enabled in this room.",                                        # 5
        "AI is disabled in this room.",                                       # 6
        "AI %s.",                                                             # 7
        "enabled",                                                            # 8
        "disabled",                                                           # 9
        "Ollama has been removed from this bot \u2014 provider is now fixed to Groq.\n"
        "Switch model: aiset model [1-7]",                                    # 10
        "Model Groq \u2192 %s\n%s",                                           # 11
        "Groq options: %s",                                                   # 12
        "No custom limit.",                                                   # 13
        "Custom history limit:",                                              # 14
        "  %s -> %s",                                                         # 15
        "Usage: aiset ulimit <jid/nick> <number>|reset\n"
        "       aiset ulimit list",                                           # 16
        "Custom limit for %s removed.",                                       # 17
        "%s doesn't have a custom limit.",                                    # 18
        "Custom limit %s -> %d messages.",                                    # 19
        "Value must be a positive number.",                                   # 20
        "All user history deleted. (%d keys)",                                # 21
        "Use: aiset reset all",                                               # 22
        "History, ulimit, & room log saved.",                                 # 23
        "History reloaded. (%d keys, %d room logs)",                          # 24
        "History Info\n"                                                      # 25
        "Dir      : %s\n"
        "Size     : %.1f KB history / %.1f KB ulimit / %.1f KB room log\n"
        "Keys     : %d user, %d room (history)\n"
        "Msg      : %d total\n"
        "Room log : %d rooms recorded, last %d messages as context\n"
        "Dirty    : history=%s room_log=%s",
        "History & room log deleted.\n"                                       # 26
        "RAM  : %d history keys, %d room logs\n"
        "Disk : %s",
        "Usage: aiset history save|load|info|clear",                          # 27
        "[Nexsus] Failed to fetch quota data.",                               # 28
        "Groq Quota \u2014 %s\n"                                              # 29
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "Model       : %s\n"
        "Requests    : %s / %s\n"
        "Tokens      : %s / %s\n"
        "Reset Req   : %s\n"
        "Reset Token : %s\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        "(data from last request)",
        "Fetching quota data from Groq...",                                   # 30
        "Groq: %s",                                                           # 31
        "key OK",                                                             # 32
        "key not set",                                                        # 33
        "Groq key reloaded: %s",                                              # 34
        "OK (%s...)",                                                         # 35
        "NOT FOUND",                                                          # 36
        "[Nexsus] AI Info %s\n"                                               # 37
        "Global  : %s\n"
        "Provider: groq (fixed \u2014 Ollama removed)\n"
        "Model   : %s%s\n"
        "Groq    : %s\n"
        "Users   : %d user, %d room\n"
        "Messages: %d total\n"
        "Ulimit  : %d custom\n"
        "Room log: %d rooms recorded (last %d messages as context)\n\n"
        "Commands:\n"
        "ai <question> | ai reset\n"
        "aiset on|off [global]\n"
        "aiset model [1-7]\n"
        "aiset ulimit <jid> <val>|reset|list\n"
        "aiset reset all\n"
        "aiset history save|load|info|clear\n"
        "aiset quota | ping | reloadkey | info",
        "Usage: aiset on|off [global] | model | ulimit | reset all | "        # 38
        "history | quota | ping | reloadkey | info",
        "Model Groq available:",                                              # 39
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501",  # 40
        "%s %s) %-14s %s",                                                    # 41
        "Switch: aiset model [%s]",                                           # 42
        "Groq API key not set. Run: ~/groq.sh setkey",                        # 43
        "Groq error: %s",                                                     # 44
        "Groq returned no response.",                                         # 45
        "Groq HTTP %d: %s",                                                   # 46
        "Cannot connect to Groq: %s",                                         # 47
        "Error: %s",                                                          # 48
        "All Groq models are rate limited. Try again later.",                 # 49
        "Key OK",                                                             # 50
        "Key not set",                                                        # 51
        "\nRoom ini : %s",                                                    # 52
        "Cuplikan obrolan room terakhir (buat referensi konteks saja, "      # 53
        "jangan dibalas satu-satu):",
    )

    def __init__(self, name):
        expansion.__init__(self, name)
        self.name            = name
        self._lock           = threading.Lock()
        self._history        = {}
        self._ulimit         = {}
        self._room_log       = {}
        self._dirty          = False
        self._room_log_dirty = False
        self._ai_enabled     = False
        self._disabled_rooms = set()
        self._groq_key       = _load_groq_key()
        self._groq_model_key = GROQ_MODEL_DEFAULT
        self._groq_quota     = {}   # simpan header quota dari response terakhir

        self._ensure_dir()
        self._load_history()
        self._load_ulimit()
        self._load_room_log()

        # fix: boot_check non-blocking via thread
        threading.Thread(target=self._boot_check, daemon=True).start()
        self._start_flush_loop()
        expansions[self.name] = self

    def dels(self):
        self._save_history()
        self._save_ulimit()
        self._save_room_log()
        if self.name in expansions:
            del expansions[self.name]

    # ── Boot ─────────────────────────────────────────────────
    def _boot_check(self):
        # Ollama sudah dihapus — satu-satunya provider sekarang Groq.
        if self._groq_key:
            self._ai_enabled = True
            mid, mdesc = GROQ_MODELS[self._groq_model_key]
            print("[nexsus:ai] Groq key found — model=%s" % mid)
        else:
            print("[nexsus:ai] WARNING: Groq key tidak ada (~/.groq_config). AI dinonaktifkan. "
                  "Jalankan: groq.sh setkey")

    # ── Persistensi ──────────────────────────────────────────
    def _ensure_dir(self):
        _os.makedirs(HISTORY_DIR, exist_ok=True)

    def _load_history(self):
        import time
        try:
            with open(HISTORY_FILE) as f:
                raw = json.load(f)
            cutoff = time.time() - HISTORY_MAX_AGE * 86400
            self._history = {
                k: [e for e in v if e.get("ts", 0) >= cutoff]
                for k, v in raw.items()
            }
            print("[nexsus:ai] History dimuat: %d key" % len(self._history))
        except Exception:
            self._history = {}

    def _load_ulimit(self):
        try:
            with open(ULIMIT_FILE) as f:
                self._ulimit = json.load(f)
            print("[nexsus:ai] Ulimit dimuat: %d entry" % len(self._ulimit))
        except Exception:
            self._ulimit = {}

    def _load_room_log(self):
        try:
            with open(ROOM_LOG_FILE) as f:
                self._room_log = json.load(f)
            print("[nexsus:ai] Room log dimuat: %d room" % len(self._room_log))
        except Exception:
            self._room_log = {}

    def _save_history(self):
        # fix: atomic write via tmp -> replace
        try:
            self._ensure_dir()
            with self._lock:
                data = {k: list(v) for k, v in self._history.items()}
            tmp = HISTORY_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            _os.replace(tmp, HISTORY_FILE)
            self._dirty = False
        except Exception as e:
            print("[nexsus:ai] Gagal save history: %s" % e)

    def _save_ulimit(self):
        try:
            self._ensure_dir()
            with self._lock:
                data = dict(self._ulimit)
            tmp = ULIMIT_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            _os.replace(tmp, ULIMIT_FILE)
        except Exception as e:
            print("[nexsus:ai] Gagal save ulimit: %s" % e)

    def _save_room_log(self):
        try:
            self._ensure_dir()
            with self._lock:
                data = {k: list(v) for k, v in self._room_log.items()}
            tmp = ROOM_LOG_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            _os.replace(tmp, ROOM_LOG_FILE)
            self._room_log_dirty = False
        except Exception as e:
            print("[nexsus:ai] Gagal save room log: %s" % e)

    def _start_flush_loop(self):
        def _loop():
            import time
            while True:
                time.sleep(HISTORY_FLUSH_INTERVAL)
                if self._dirty:
                    self._save_history()
                if self._room_log_dirty:
                    self._save_room_log()
        threading.Thread(target=_loop, daemon=True).start()

    # ── Room log — rekam & ambil konteks ─────────────────────
    def _strip_mention(self, body, nick_bot):
        # fix: hilangkan prefix "botNick:" / "botNick," / "botNick>" dari body,
        # supaya nick bot sendiri tidak ikut kebawa jadi "topik" pas dikirim
        # ke AI atau direkam ke room log. Core NexsusBot cuma strip prefix ini
        # di variabel internal (temp) buat nentuin command, bukan di body yang
        # dikirim ke handler "01eh" -- jadi harus di-strip manual di sini.
        if not body or not nick_bot:
            return body
        for sep in (":", ",", ">"):
            prefix = nick_bot + sep
            if body.startswith(prefix):
                return body[len(prefix):].lstrip()
        return body

    def _log_room_message(self, room, nick, body):
        import time
        if not room or not body:
            return
        text = body if len(body) <= ROOM_MSG_MAXLEN else (body[:ROOM_MSG_MAXLEN] + "...")
        with self._lock:
            log = self._room_log.setdefault(room, [])
            log.append({"nick": nick or "?", "body": text, "ts": time.time()})
            if len(log) > ROOM_LOG_MAX:
                self._room_log[room] = log[-ROOM_LOG_MAX:]
            self._room_log_dirty = True

    def _get_room_context(self, room, limit=ROOM_CTX_LIMIT, skip_last=False):
        with self._lock:
            log = list(self._room_log.get(room, []))
        if skip_last and log:
            log = log[:-1]
        log = log[-limit:]
        return ["[%s]: %s" % (e["nick"], e["body"]) for e in log]

    # ── Helpers ──────────────────────────────────────────────
    def _get_room_key(self, room_jid):
        return "room:%s" % room_jid

    def _get_room_limit(self, room_jid):
        # fix: cek custom ulimit per room, fallback 20
        return self._ulimit.get("room:" + room_jid, 20)

    def _get_provider_label(self):
        mid, mdesc = GROQ_MODELS[self._groq_model_key]
        return "groq/%s" % mdesc

    # fix: pakai sBase[] bukan hardcode string
    def _is_pm(self, stype):   return stype == sBase[0]
    def _is_room(self, stype): return stype == sBase[1]

    def _get_user_id(self, source):
        # fix: source[2]=nick di room, source[1]=JID, bukan source[0]
        return source[2] if source[2] else source[1]

    def _get_access(self, stype, source):
        try:
            return get_access(source[1], source[2])
        except Exception:
            # fix: fail-closed, bukan fail-open. exception saat verifikasi
            # akses harus dianggap "tidak ada akses", bukan "anggap level 1".
            return 0

    # fix: resolve nick -> JID milik user yang sedang ngomong, supaya key
    # yang dipakai untuk lookup ulimit konsisten dengan key yang dipakai
    # _resolve_target saat admin nge-set ulimit (yang juga JID-based).
    def _resolve_user_jid(self, stype, source):
        if self._is_room(stype) and source[2]:
            room = source[1]
            if room in Chats:
                user = Chats[room].get_user(source[2])
                if user and user.source:
                    return user.source.lower()
            # fallback: gagal resolve, pakai nick apa adanya
            return source[2].lower()
        return source[1].lower() if source[1] else (source[2] or "")

    def _get_history_limit(self, stype, source):
        user_id = self._get_user_id(source)
        jid     = self._resolve_user_jid(stype, source)
        # fix: cek key JID dulu (key yang dipakai aiset ulimit saat nge-set),
        # baru fallback ke key nick lama untuk backward-compat data existing.
        if jid in self._ulimit:
            return self._ulimit[jid]
        if user_id in self._ulimit:
            return self._ulimit[user_id]
        acc = self._get_access(stype, source)
        for threshold, limit in HISTORY_BY_ACCESS:
            if acc >= threshold:
                return limit
        return 0

    def _check_pm_access(self, source):
        # fix: >= 7, bukan >= 1
        return Galist.get(source[1].lower(), 0) >= 7

    def _is_ai_allowed(self, stype, source):
        if not self._ai_enabled:
            return False
        if self._get_history_limit(stype, source) == 0:
            return False
        return True

    def _get_history(self, user_id):
        return self._history.get(user_id, [])

    def _add_history(self, user_id, role, content, limit):
        import time
        with self._lock:
            h = self._history.setdefault(user_id, [])
            h.append({"role": role, "content": content, "ts": time.time()})
            if limit < 9999:
                max_entries = limit * 2
                # fix: h[-0:] di Python == h[0:] (seluruh list), bukan kosong.
                # limit == 0 harus berarti "tidak nyimpen apa-apa", bukan
                # "trimming dimatikan tanpa sengaja".
                if max_entries <= 0:
                    self._history[user_id] = []
                elif len(h) > max_entries:
                    self._history[user_id] = h[-max_entries:]
            self._dirty = True

    def _reset_history(self, user_id):
        with self._lock:
            self._history.pop(user_id, None)
            self._dirty = True

    def _reset_all_history(self):
        with self._lock:
            self._history.clear()
            self._dirty = True

    def _resolve_target(self, target, source):
        # cari JID asli dari nick via Chats
        room = source[1] if source else None
        if room and room in Chats:
            user = Chats[room].get_user(target)
            if user and user.source:
                return user.source.lower(), target
        # fallback: cari di semua room
        for room_jid, conf in Chats.items():
            user = conf.get_user(target)
            if user and user.source:
                return user.source.lower(), target
        return target.lower(), target


    # Nama bahasa buat instruksi ke model -- deteksi yang jalan cuma buat
    # AnsBase (LocalizationContext) itu boilerplate, bahasa JAWA yang
    # dipakai model ditentukan di sini.
    _LANG_MODEL_NAMES = {
        "id": "Indonesia", "jv": "Jawa", "en": "Inggris", "ar": "Arab",
        "ru": "Rusia", "uk": "Ukraina", "bg": "Bulgaria", "el": "Yunani",
        "th": "Thailand", "hi": "Hindi", "zh": "Mandarin", "ja": "Jepang",
        "ko": "Korea", "fa": "Persia", "de": "Jerman", "fr": "Perancis",
        "es": "Spanyol", "pt": "Portugis", "it": "Italia", "tr": "Turki",
    }

    # ── Deteksi bahasa otomatis dari isi pesan ──
    _LANG_SCRIPTS = {
        "ar": "\u0600-\u06FF",       # Arab
        "he": "\u0590-\u05FF",       # Ibrani
        "hi": "\u0900-\u097F",       # Devanagari (Hindi/Marathi)
        "zh": "\u4E00-\u9FFF",       # CJK Han (Chinese/Japanese)
        "ru": "\u0400-\u04FF",       # Cyrillic (Russian/Ukrainian/Bulgarian)
        "uk": "\u0400-\u04FF",
        "bg": "\u0400-\u04FF",
        "el": "\u0370-\u03FF",       # Greek
        "th": "\u0E00-\u0E7F",       # Thai
        "jv": "\ua980-\ua9df",       # Aksara Jawa (Javanese script)
        "hi_k": None,
    }

    # Kata umum per bahasa untuk deteksi Latin-script
    _LANG_KEYWORDS = {
        "id": ("yang", "dan", "ini", "itu", "tidak", "bukan", "saya", "aku",
               "kamu", "kita", "mereka", "dengan", "untuk", "dari", "ada",
               "apa", "kenapa", "bagaimana", "boleh", "gimana", "nggak",
               "udah", "lah", "dong", "sih", "kok", "banget", "makasih"),
        "jv": ("sing", "lan", "iki", "iku", "ora", "dadi", "kowe", "karo",
               "saka", "jare", "piye", "gak", "wis", "mbak", "ndak", "mbuh",
               "lur", "cak", "aja", "padha", "cah", "dereng", "mangan",
               "lunga", "menyang", "saiki", "mengko", "tak", "wae", "tenan",
               "saestu", "nggih", "ngoten", "menapa", "cuman", "nanging",
               "dangu", "arep", "krungu", "kula", "panjenengan"),
        "en": ("the", "and", "this", "that", "what", "how", "why", "who",
               "where", "when", "is", "are", "was", "were", "you", "your",
               "my", "me", "we", "they", "can", "could", "should", "would",
               "please", "thanks", "hello", "hey", "bro", "dude"),
        "es": ("que", "como", "por", "para", "con", "una", "pero", "mas",
               "muy", "gracias", "hola", "bueno", "donde", "cuando", "quien",
               "este", "esta", "eso", "tambien", "puede", "tiene"),
        "pt": ("que", "como", "para", "com", "uma", "mas", "muito", "obrigado",
               "ola", "bom", "onde", "quando", "quem", "este", "esta", "isso",
               "tambem", "pode", "tem", "nao", "voce", "mais"),
        "fr": ("que", "comment", "pour", "avec", "une", "mais", "plus",
               "tres", "merci", "bonjour", "bon", "ou", "quand", "qui",
               "ce", "cette", "aussi", "peut", "etre", "dans", "vous",
               "est", "sont", "pas", "mais", "bien"),
        "de": ("das", "wie", "und", "ist", "nicht", "ein", "eine", "auch",
               "noch", "danke", "hallo", "gut", "wo", "wann", "wer",
               "dies", "diese", "kann", "muss", "soll", "von", "mit",
               "auf", "für", "aber", "sehr"),
        "it": ("che", "come", "per", "con", "una", "ma", "piu", "grazie",
               "ciao", "bene", "dove", "quando", "chi", "questo", "questa",
               "anche", "puo", "essere", "nel", "non", "piu", "siamo"),
        "ru": ("и", "что", "это", "не", "на", "я", "ты", "он", "она",
               "мы", "вы", "они", "как", "а", "но", "по", "из", "для",
               "при", "о", "от", "до", "же", "бы", "так", "вот", "тут"),
        "tr": ("bir", "bu", "su", "icin", "ile", "ama", "daha", "cok",
               "tesekkur", "merhaba", "iyi", "nerede", "ne zaman", "kim",
               "bu", "simdi", "de", "da", "mi", "mı", "sana", "ben"),
        "ar": ("في", "من", "على", "أن", "هل", "ما", "هذا", "هذه",
               "التي", "مع", "عن", "لا", "نعم", "شكرا", "مرحبا",
               "أنا", "أنت", "هو", "هي", "نحن", "هم"),
        "hi": ("है", "के", "का", "की", "में", "से", "को", "पर",
               "यह", "वह", "क्या", "कैसे", "क्यों", "नमस्ते", "धन्यवाद",
               "मैं", "तुम", "हम", "वे", "और", "लेकिन", "हां", "नहीं"),
        "zh": ("的", "了", "是", "在", "我", "你", "他", "她",
               "它", "们", "这", "那", "什么", "怎么", "为什么",
               "请", "谢谢", "你好", "是的", "不是", "有", "没"),
        "ja": ("の", "に", "は", "を", "た", "が", "で", "て",
               "これ", "それ", "あれ", "なに", "どう", "なぜ",
               "ありがとう", "こんにちは", "はい", "いいえ"),
        "ko": ("의", "에", "는", "을", "이", "가", "에서", "으로",
               "이것", "그것", "무엇", "어떻게", "왜",
               "감사합니다", "안녕하세요", "네", "아니요"),
        "fa": ("در", "از", "بر", "که", "این", "آن", "چه", "چطور",
               "چرا", "ممنون", "سلام", "من", "تو", "او", "ما", "آنها",
               "و", "اما", "با", "برای", "هست", "نیست"),
    }

    def _detect_lang(self, text):
        """Deteksi bahasa dari teks. Kembalikan kode bahasa atau None."""
        if not text or len(text.strip()) < 3:
            return None
        # 1. Cek script non-Latin (lebih reliable)
        for code, rng in self._LANG_SCRIPTS.items():
            if rng and re.search('[' + rng + ']', text):
                return code
        # 2. Cek Latin-script: hitung keyword per bahasa
        words = set(re.findall(r'[a-zA-Z\']+',
                               text.lower()))
        if not words:
            return None
        best_code, best_score = None, 0
        for code, kws in self._LANG_KEYWORDS.items():
            score = len(words & set(kws))
            if score > best_score:
                best_score = score
                best_code = code
        # Jawa vs Indonesia: banyak kata identik (aku, apa, lan, sing), jadi
        # kalau skor Jawa sama dengan pemenang sementara, menangin Jawa.
        # Syaratnya skor Jawa > 0 -- kalau 0 (teks murni bahasa lain),
        # jangan diambil alih.
        if best_code != "jv":
            jv_score = len(words & set(self._LANG_KEYWORDS["jv"]))
            if jv_score and jv_score >= best_score:
                best_code, best_score = "jv", jv_score
        return best_code if best_score >= (1 if best_code == "jv" else 2) else None

    def _lang_hint(self, lang):
        """Instruksi bahasa buat model. Terdeteksi = HARUS dipakai.

        Sebelumnya SYSTEM_PROMPT cuma nyuruh 'mirror bahasa user', tapi
        cuplikan room context bisa berbahasa lain dan model ikut kesana --
        pesan Jawa dijawab Inggris. Dengan instruksi eksplisit di sini,
        bahasa hasil _detect_lang yang menang.
        """
        name = self._LANG_MODEL_NAMES.get(lang)
        if not name:
            return None
        return ("Wajib menjawab SEPENUHNYA dalam bahasa %s, apa pun bahasa "
                "cuplikan obrolan atau pesan sebelumnya di konteks. "
                "(Jangan campur bahasa lain kecuali kutipan/kode.)" % name)

    def _reply_lang(self, text, stype, source, disp):
        """Kirim reply dengan bahasa yang terdeteksi dari teks user."""
        lang = self._detect_lang(text)
        if lang and lang != "en":
            try:
                locale = self._locale.get(lang)
                if locale:
                    # pakai bahasa terdeteksi
                    pass
            except Exception:
                pass
        return lang

    # ── Groq call ─────────────────────────────────────────────
    # fix: model_key sekarang parameter eksplisit, bukan baca self._groq_model_key.
    # Ini menghindari race condition saat beberapa thread (tiap /ai dan tiap
    # mention jalan di thread terpisah) saling timpa instance attribute waktu
    # proses fallback rate-limit berlangsung bersamaan.
    def _call_groq(self, user_id, prompt, limit, model_key=None,
                   room_context=None, lang=None):
        if model_key is None:
            model_key = self._groq_model_key
        if not self._groq_key:
            return None, self.AnsBase[43]
        if len(prompt) > 1200:
            prompt = prompt[:1200] + "..."
        with self._lock:
            history = list(self._get_history(user_id))
        clean_history = [{"role": e["role"], "content": e["content"]} for e in history]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        lang_hint = self._lang_hint(lang)
        if lang_hint:
            # system message terpisah, bukan diselipin ke SYSTEM_PROMPT --
            # SYSTEM_PROMPT dipakai bersama, ini khusus per-pesan.
            messages.append({"role": "system", "content": lang_hint})
        if room_context:
            messages.append({
                "role": "system",
                "content": (self.AnsBase[53] + "\n" + "\n".join(room_context))
            })
        messages += clean_history
        messages.append({"role": "user", "content": prompt})
        model_id, _ = GROQ_MODELS[model_key]
        payload = json.dumps({
            "model":       model_id,
            "messages":    messages,
            "max_tokens":  800,
            "temperature": 0.7,
            "stream":      False,
        }).encode("utf-8")
        req = urllib.request.Request(
            GROQ_API_BASE,
            data=payload,
            headers={
                "Content-Type":  "application/json",
                "Authorization": "Bearer %s" % self._groq_key,
                "User-Agent":    "Mozilla/5.0 (compatible; NexsusBot/8.0)",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                # baca header quota sebelum close
                self._groq_quota = {
                    "limit_req":  resp.headers.get("x-ratelimit-limit-requests",    "-"),
                    "remain_req": resp.headers.get("x-ratelimit-remaining-requests", "-"),
                    "limit_tok":  resp.headers.get("x-ratelimit-limit-tokens",       "-"),
                    "remain_tok": resp.headers.get("x-ratelimit-remaining-tokens",   "-"),
                    "reset_req":  resp.headers.get("x-ratelimit-reset-requests",     "-"),
                    "reset_tok":  resp.headers.get("x-ratelimit-reset-tokens",       "-"),
                }
                data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                return None, self.AnsBase[44] % data["error"].get("message", "unknown")
            result = data["choices"][0]["message"]["content"].strip()
            # strip blok <think>...</think> (Qwen3 chain-of-thought)
            import re as _re
            result = _re.sub(r"<think>.*?</think>", "", result, flags=_re.DOTALL).strip()
            result = "".join(c for c in result if c >= " " or c in "\n\t")
            if len(result) > 1500:
                result = result[:1497] + "..."
            if not result:
                return None, self.AnsBase[45]
            self._add_history(user_id, "user",      prompt, limit)
            self._add_history(user_id, "assistant", result, limit)
            return result, None
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                msg = json.loads(body)["error"]["message"]
            except Exception:
                msg = body[:200]
            if e.code == 429:
                # fix: pakai model_key parameter lokal, bukan self._groq_model_key
                # yang bisa sudah berubah ditimpa thread lain saat ini dibaca.
                return None, "__RATE_LIMIT__:%s" % model_key
            return None, self.AnsBase[46] % (e.code, msg)
        except urllib.error.URLError as e:
            return None, self.AnsBase[47] % e.reason
        except Exception as e:
            return None, self.AnsBase[48] % str(e)

    # ── Dispatch provider ─────────────────────────────────────
    # Ollama sudah dihapus — tidak ada lagi fallback ke provider lain.
    # Urutan fallback antar model Groq: model aktif -> model 2 (8B, limit tinggi) -> dst.
    GROQ_FALLBACK_ORDER = ["7", "6", "3", "4", "5", "2", "1"]  # 7=8B limit tinggi dulu, lalu dari kecil ke besar

    def _call_ai(self, user_id, prompt, limit, room_context=None, lang=None):
        # fix: snapshot lokal, BUKAN mutate self._groq_model_key. Sebelumnya
        # fungsi ini mengubah lalu "restore" instance attribute ini untuk
        # logic fallback — tapi karena /ai dan mention jalan di thread
        # terpisah, thread lain bisa baca/timpa nilai itu di tengah proses
        # dan bikin user lain ketuker model atau setting global ke-overwrite.
        current_key = self._groq_model_key
        tried = set()

        result, err = self._call_groq(user_id, prompt, limit, model_key=current_key,
                                      room_context=room_context, lang=lang)
        tried.add(current_key)

        # fallback antar model Groq jika rate limit
        while err and err.startswith("__RATE_LIMIT__"):
            failed_key = err.split(":", 1)[1]
            next_key = None
            for k in self.GROQ_FALLBACK_ORDER:
                if k not in tried and k != failed_key:
                    next_key = k
                    break

            if not next_key:
                # semua model Groq kena rate limit — tidak ada provider lain lagi
                return None, self.AnsBase[49]

            print("[nexsus:ai] Rate limit model %s, fallback ke model %s" % (failed_key, next_key))
            tried.add(next_key)
            result, err = self._call_groq(user_id, prompt, limit, model_key=next_key,
                                          room_context=room_context, lang=lang)

        return result, err

    # ── Normalisasi jawaban: buang label pembicara buatan model ──
    # Model Groq sering meniru format room context ("[nick]: pesan") dan
    # memulai jawabannya dengan "[nick]: ".  Core NexsusBot sudah membalut
    # jawaban room dengan "senderNick: " (Answer() -> Message()), jadi label
    # buatan model bikin prefix dobel: "ρay: [ρay]: Halo! ...".
    # Dipotong HANYA kalau: (a) ada di posisi paling depan, dan (b) isinya
    # persis nick yang minta atau nick bot di room itu.  Teks biasa yang
    # kebetulan menyebut nama di tengah kalimat tidak tersentuh.
    _SPEAKER_PREFIX_RE = re.compile(r"^\s*\[([^\[\]\n]{1,40})\]:\s*")

    def _strip_speaker_prefix(self, text, nicks):
        if not text:
            return text
        allow = {str(n).strip().lower() for n in nicks if n}
        if not allow:
            return text
        m = self._SPEAKER_PREFIX_RE.match(text)
        if m and m.group(1).strip().lower() in allow:
            return text[m.end():].lstrip()
        return text

    # Sisa "[nick]" di mana pun dalam jawaban (biasanya vokatif: "Halo,
    # [raijo]?") dibikin polos -- kurung siku yang dibuang, nama + tanda
    # baca sesudahnya dipertahankan.  Hanya nick yang dikenal (yang minta,
    # nick bot, anggota room yang muncul di room log); "[DONE]", "[1/2]",
    # atau nick orang lain tidak tersentuh.
    _NICK_IN_BRACKETS_RE = re.compile(r"\[([^\[\]\n]{1,40})\]")

    def _strip_bracket_labels(self, text, nicks):
        if not text:
            return text
        allow = {str(n).strip().lower() for n in nicks if n}
        if not allow:
            return text
        def _rep(m):
            inner = m.group(1).strip()
            return inner if inner.lower() in allow else m.group(0)
        return self._NICK_IN_BRACKETS_RE.sub(_rep, text)

    # ── Chunked sender ────────────────────────────────────────
    def _send_chunked(self, text, stype, source, disp):
        import time
        if len(text) <= CHUNK_SIZE:
            Answer(text, stype, source, disp)
            return
        words  = text.split()
        chunks = []
        cur    = ""
        for w in words:
            if len(cur) + len(w) + 1 > CHUNK_SIZE:
                chunks.append(cur.strip())
                cur = w
            else:
                cur = (cur + " " + w).strip() if cur else w
        if cur:
            chunks.append(cur.strip())
        total = len(chunks)
        for i, chunk in enumerate(chunks, 1):
            Answer("(%d/%d) %s" % (i, total, chunk), stype, source, disp)
            if i < total:
                time.sleep(0.8)

    # ── AI worker ─────────────────────────────────────────────
    def _ai_worker(self, user_id, prompt, limit, stype, source, disp,
                   room_key=None, nick=None, room_context=None):
        # fix: jika room_key ada, pakai room_key sebagai history key
        # _call_ai akan add_history ke history_key, bukan user_id
        history_key    = room_key if room_key else user_id
        tagged_prompt  = ("[%s]: %s" % (nick, prompt)) if nick else prompt

        # fix: deteksi bahasa dari pesan user, set locale context thread ini
        # supaya reply (termasuk error message) ikut bahasa user.
        detected_lang = self._detect_lang(prompt)
        locale_ctx = None
        if detected_lang and detected_lang != "en":
            try:
                from nxs_l10n import LocalizationContext
                locale_ctx = LocalizationContext(detected_lang)
                locale_ctx.__enter__()
            except Exception:
                locale_ctx = None

        try:
            result, err = self._call_ai(history_key, tagged_prompt, limit,
                                        room_context=room_context,
                                        lang=detected_lang)
            if err:
                Answer(self.AnsBase[3] % err, stype, source, disp)
                return
            # buang label "[nick]:" buatan model di depan jawaban, supaya
            # tidak dobel dengan prefix yang ditambahkan core (Answer()),
            # lalu buang sisa kurung siku di sekitar nick yang dikenal.
            bot_nick = None
            room_jid = source[1] if self._is_room(stype) else None
            if room_jid:
                try:
                    if room_jid in Chats:
                        bot_nick = get_nick(room_jid)
                except Exception:
                    bot_nick = None
            known_nicks = [nick, source[2], bot_nick]
            if room_jid:
                try:
                    known_nicks += [e.get("nick") for e in self._room_log.get(room_jid, [])]
                except Exception:
                    pass
            result = self._strip_speaker_prefix(result, known_nicks)
            result = self._strip_bracket_labels(result, known_nicks)
            if not result:
                Answer(self.AnsBase[45], stype, source, disp)
                return
            self._send_chunked(result, stype, source, disp)
        finally:
            if locale_ctx:
                try:
                    locale_ctx.__exit__(None, None, None)
                except Exception:
                    pass

    # ── /ai ───────────────────────────────────────────────────
    def command_ai(self, stype, source, body, disp):
        """/ai <pertanyaan> | reset"""
        if self._is_pm(stype) and not self._check_pm_access(source):
            return
        if self._is_room(stype) and source[1] in self._disabled_rooms:
            return
        if not self._ai_enabled:
            Answer(self.AnsBase[0], stype, source, disp)
            return

        user_id = self._get_user_id(source)
        limit   = self._get_history_limit(stype, source)
        cmd     = (body or "").strip()

        if cmd.lower() == "reset":
            self._reset_history(user_id)
            Answer(self.AnsBase[1], stype, source, disp)
            return

        if not cmd:
            history_count = len(self._get_history(user_id)) // 2
            limit_str     = "unlimited" if limit >= 9999 else str(limit)
            Answer(
                self.AnsBase[2] % (
                    AI_VERSION,
                    self._get_provider_label(),
                    history_count,
                    limit_str,
                ),
                stype, source, disp
            )
            return

        # kalau dipakai di dalam room, sertakan cuplikan obrolan room
        # sebagai konteks juga (bukan cuma saat mention).
        room_context = None
        if self._is_room(stype):
            room_context = self._get_room_context(source[1])

        threading.Thread(
            target=self._ai_worker,
            args=(user_id, cmd, limit, stype, source, disp),
            kwargs={"room_context": room_context},
            daemon=True,
        ).start()

    # ── mention handler ───────────────────────────────────────
    def ai_01eh(self, stanza, isConf, stype, source, body, isToBs, disp):
        # fix: strip prefix "botNick:" dari body -- core cuma strip ini di
        # variabel internal (temp), bukan di body yang dikirim ke handler
        # "01eh". Tanpa ini, nick bot sendiri ikut kebawa jadi "topik" pas
        # direkam ke room log maupun dikirim sebagai prompt ke AI.
        room_for_nick = source[1] if isConf else None
        nick_bot = get_nick(room_for_nick) if room_for_nick in Chats else None
        clean_body = self._strip_mention(body, nick_bot)

        # Rekam SEMUA posting di room (bukan cuma yang mention bot),
        # dipakai sebagai konteks obrolan untuk AI nanti.
        if isConf and source[1] and clean_body:
            self._log_room_message(source[1], source[2], clean_body)

        if not isToBs or not isConf:
            return
        if source[1] in self._disabled_rooms:
            return
        if not self._ai_enabled:
            return
        # fix: sebelumnya mention sama sekali tidak dicek access level
        # individu (cuma dicek _disabled_rooms & _ai_enabled global), jadi
        # siapa pun yang bisa posting & mention bot otomatis dapat respons
        # AI terlepas dari access level mereka. _is_ai_allowed sudah ada
        # tapi tidak pernah dipanggil di manapun — sekarang dipakai di sini
        # supaya konsisten dengan gating /ai (yang minimal access level 1).
        if not self._is_ai_allowed(stype, source):
            return
        prompt = (clean_body or "").strip()
        if not prompt:
            return
        first_word = prompt.split()[0].lower()
        if first_word in ("ai", "aiset"):
            return
        user_id  = self._get_user_id(source)
        nick     = source[2] if source[2] else user_id
        room_jid = source[1]
        room_key = self._get_room_key(room_jid)
        limit    = self._get_room_limit(room_jid)
        # skip_last=True: pesan yang sedang diproses ini sudah kepencet
        # ke room log barusan (di atas), jangan didobel di context block.
        room_context = self._get_room_context(room_jid, skip_last=True)
        threading.Thread(
            target=self._ai_worker,
            args=(user_id, prompt, limit, stype, source, disp),
            kwargs={"room_key": room_key, "nick": nick, "room_context": room_context},
            daemon=True,
        ).start()

    # ── /aiset ────────────────────────────────────────────────
    def command_aiset(self, stype, source, body, disp):
        """/aiset on|off|model|ulimit|reset|history|quota|ping|reloadkey|info"""
        args = (body or "").strip().split()
        cmd  = args[0].lower() if args else "info"
        sub  = args[1].lower() if len(args) > 1 else ""

        # -- on / off ─────────────────────────────────────────
        if cmd in ("on", "off"):
            is_on = cmd == "on"
            if sub == "global":
                self._ai_enabled = is_on
                if is_on:
                    self._disabled_rooms.clear()
                Answer(self.AnsBase[4] % (self.AnsBase[8] if is_on else self.AnsBase[9]),
                       stype, source, disp)
            elif self._is_room(stype):
                room = source[1]
                if is_on:
                    self._disabled_rooms.discard(room)
                    Answer(self.AnsBase[5], stype, source, disp)
                else:
                    self._disabled_rooms.add(room)
                    Answer(self.AnsBase[6], stype, source, disp)
            else:
                self._ai_enabled = is_on
                Answer(self.AnsBase[7] % (self.AnsBase[8] if is_on else self.AnsBase[9]),
                       stype, source, disp)

        # -- provider (deprecated, Ollama dihapus) ─────────────
        elif cmd == "provider":
            Answer(self.AnsBase[10], stype, source, disp)

        # -- model ────────────────────────────────────────────
        elif cmd == "model":
            valid_keys = "|".join(sorted(GROQ_MODELS.keys()))
            if not sub:
                lines = [self.AnsBase[39]]
                lines.append(self.AnsBase[40])
                for k in sorted(GROQ_MODELS.keys()):
                    mid, mdesc = GROQ_MODELS[k]
                    marker = ">" if k == self._groq_model_key else " "
                    lines.append(self.AnsBase[41] % (marker, k, mdesc, mid))
                lines.append(self.AnsBase[40])
                lines.append(self.AnsBase[42] % valid_keys)
                Answer("\n".join(lines), stype, source, disp)
            elif sub in GROQ_MODELS:
                self._groq_model_key = sub
                mid, mdesc = GROQ_MODELS[sub]
                Answer(self.AnsBase[11] % (mdesc, mid), stype, source, disp)
            else:
                Answer(self.AnsBase[12] % valid_keys, stype, source, disp)

        # -- ulimit ───────────────────────────────────────────
        elif cmd == "ulimit":
            if sub == "list":
                if not self._ulimit:
                    Answer(self.AnsBase[13], stype, source, disp)
                else:
                    lines = [self.AnsBase[14]]
                    for uid, lim in sorted(self._ulimit.items()):
                        lines.append(self.AnsBase[15] % (uid, "unlimited" if lim >= 9999 else str(lim)))
                    Answer("\n".join(lines), stype, source, disp)
                return
            if len(args) < 3:
                Answer(self.AnsBase[16], stype, source, disp)
                return
            target  = args[1]
            val_str = args[2].lower()
            jid, display = self._resolve_target(target, source)
            if val_str == "reset":
                removed = self._ulimit.pop(jid, None)
                self._save_ulimit()
                Answer(
                    self.AnsBase[17] % display if removed is not None
                    else self.AnsBase[18] % display,
                    stype, source, disp
                )
            else:
                try:
                    val = int(val_str)
                    if val < 1:
                        raise ValueError
                    self._ulimit[jid] = val
                    self._save_ulimit()
                    Answer(self.AnsBase[19] % (display, val), stype, source, disp)
                except ValueError:
                    Answer(self.AnsBase[20], stype, source, disp)

        # -- reset ────────────────────────────────────────────
        elif cmd == "reset":
            if sub == "all":
                total = len(self._history)
                self._reset_all_history()
                Answer(self.AnsBase[21] % total, stype, source, disp)
            else:
                Answer(self.AnsBase[22], stype, source, disp)

        # -- history ──────────────────────────────────────────
        elif cmd == "history":
            if sub == "save":
                self._save_history()
                self._save_ulimit()
                self._save_room_log()
                Answer(self.AnsBase[23], stype, source, disp)
            elif sub == "load":
                self._load_history()
                self._load_ulimit()
                self._load_room_log()
                Answer(self.AnsBase[24] % (
                        len(self._history), len(self._room_log)
                    ),
                    stype, source, disp
                )
            elif sub == "info":
                h_size = _os.path.getsize(HISTORY_FILE)  if _os.path.exists(HISTORY_FILE)  else 0
                u_size = _os.path.getsize(ULIMIT_FILE)   if _os.path.exists(ULIMIT_FILE)   else 0
                r_size = _os.path.getsize(ROOM_LOG_FILE) if _os.path.exists(ROOM_LOG_FILE) else 0
                Answer(self.AnsBase[25] % (
                        HISTORY_DIR,
                        h_size / 1024,
                        u_size / 1024,
                        r_size / 1024,
                        sum(1 for k in self._history if not k.startswith("room:")),
                        sum(1 for k in self._history if k.startswith("room:")),
                        sum(len(v) for v in self._history.values()) // 2,
                        len(self._room_log),
                        ROOM_CTX_LIMIT,
                        "ya" if self._dirty else "tidak",
                        "ya" if self._room_log_dirty else "tidak",
                    ),
                    stype, source, disp
                )
            elif sub == "clear":
                total_ram = len(self._history)
                total_room = len(self._room_log)
                self._reset_all_history()
                with self._lock:
                    self._room_log.clear()
                    self._room_log_dirty = True
                removed = []
                for f in (HISTORY_FILE, ULIMIT_FILE, ROOM_LOG_FILE):
                    if _os.path.exists(f):
                        _os.remove(f)
                        removed.append(_os.path.basename(f))
                self._dirty = False
                self._room_log_dirty = False
                Answer(self.AnsBase[26] % (
                        total_ram, total_room,
                        ", ".join(removed) if removed else "tidak ada file",
                    ),
                    stype, source, disp
                )
            else:
                Answer(self.AnsBase[27], stype, source, disp)

        # -- quota ───────────────────────────────────────────
        elif cmd == "quota":
            if not self._groq_quota:
                # belum ada data — kirim 1 request kecil dulu untuk ambil header
                def _fetch_quota():
                    self._call_groq("__quota_check__", "ping", 1)
                    # fix: jangan biarkan probe ini numpuk permanen di history,
                    # ini bukan percakapan asli, cuma buat baca header quota.
                    self._reset_history("__quota_check__")
                    q = self._groq_quota
                    if not q:
                        Answer(self.AnsBase[28], stype, source, disp)
                        return
                    mid, mdesc = GROQ_MODELS[self._groq_model_key]
                    Answer(self.AnsBase[29] % (
                            mdesc,
                            mid,
                            q.get("remain_req", "-"), q.get("limit_req", "-"),
                            q.get("remain_tok", "-"), q.get("limit_tok", "-"),
                            q.get("reset_req",  "-"),
                            q.get("reset_tok",  "-"),
                        ),
                        stype, source, disp
                    )
                threading.Thread(target=_fetch_quota, daemon=True).start()
                Answer(self.AnsBase[30], stype, source, disp)
            else:
                q = self._groq_quota
                mid, mdesc = GROQ_MODELS[self._groq_model_key]
                Answer(
                    self.AnsBase[29] % (
                        mdesc,
                        mid,
                        q.get("remain_req", "-"), q.get("limit_req", "-"),
                        q.get("remain_tok", "-"), q.get("limit_tok", "-"),
                        q.get("reset_req",  "-"),
                        q.get("reset_tok",  "-"),
                    ),
                    stype, source, disp
                )

        # -- ping ─────────────────────────────────────────────
        elif cmd == "ping":
            Answer(
                self.AnsBase[31] % (self.AnsBase[32] if self._groq_key else self.AnsBase[33]),
                stype, source, disp
            )

        # -- reloadkey ────────────────────────────────────────
        elif cmd == "reloadkey":
            self._groq_key = _load_groq_key()
            Answer(
                self.AnsBase[34] % (
                    self.AnsBase[35] % self._groq_key[:8] if self._groq_key else self.AnsBase[36]
                ),
                stype, source, disp
            )

        # -- info ─────────────────────────────────────────────
        elif cmd == "info":
            total_users   = sum(1 for k in self._history if not k.startswith("room:"))
            total_rooms   = sum(1 for k in self._history if k.startswith("room:"))
            total_msgs    = sum(len(v) for v in self._history.values()) // 2
            groq_status   = self.AnsBase[50] if self._groq_key else self.AnsBase[51]
            room_str = ""
            if self._is_room(stype):
                room_str = self.AnsBase[52] % (
                    "OFF" if source[1] in self._disabled_rooms else "ON"
                )
            mid, mdesc = GROQ_MODELS[self._groq_model_key]
            model_str = "groq/%s (%s)" % (mdesc, mid)
            Answer(self.AnsBase[37] % (
                    AI_VERSION,
                    "ON" if self._ai_enabled else "OFF",
                    model_str,
                    room_str,
                    groq_status,
                    total_users,
                    total_rooms,
                    total_msgs,
                    len(self._ulimit),
                    len(self._room_log),
                    ROOM_CTX_LIMIT,
                ),
                stype, source, disp
            )

        else:
            Answer(self.AnsBase[38], stype, source, disp)

    commands = (
        (command_ai,    "ai",    1,),
        (command_aiset, "aiset", 7,),
    )

    handlers = (
        (ai_01eh, "01eh"),
    )
