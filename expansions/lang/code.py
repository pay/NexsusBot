# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "lang" # /code.py v.x8
#  Ported to Python 3 / slixmpp by Nexsus Project 2026
#
# Pilih bahasa reply bot untuk user ini saja (per room, per nick).
#
#   :lang            -> tampilkan bahasa sekarang + daftar yang tersedia
#   :lang id         -> pakai Bahasa Indonesia
#   :lang en         -> pakai English
#   :lang auto       -> kembali ke deteksi otomatis (tag <lang/> dari client)
#   :lang list       -> siapa saja di room ini yang sudah pilih bahasa
#
# Prioritas di getLang(): pilihan di sini > <lang/> dari presence > DefLANG.

import os

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AnsBase = (
		"\U0001f4cb Bahasa sekarang: %s\n\U0001f4c4 Dipakai: %s\n\U0001f50d Codes: %s\n\U0001f4a1gdipakai juga nama: %s",  # 0
		"\u2705 Bahasa lo sekarang: %s.",                                                      # 1
		"\u274c Kode bahasa nggak dikenal: %s.\n\U0001f50d Codes: %s",                       # 2
		"\u274c Gagal nyimpen pilihan bahasa.",                                                # 3
		"\u2139\ufe0f Closing the loop: ':lang auto' buat balik ke deteksi otomatis.",       # 4
		"\U0001f4cb Bahasa di room ini:\n%s",                                                  # 5
		"\u2139\ufe0f Belum ada yang pilih bahasa di sini.",                                  # 6
		"\u274c Gagal baca database bahasa.",                                                 # 7
	)

	# ── helpers ────────────────────────────────────────────────

	def _codes(self):
		"""Kode bahasa yang punya file locale di ekspansi manapun.

		English sengaja tidak punya file ans.en.json - string Inggris
		ditulis langsung di AnsBase tiap ekspansi dan jadi fallback.  Jadi
		'en' selalu tersedia walau tidak ada file-nya.
		"""
		exp_root = "expansions"
		found = {"en"}
		try:
			for name in os.listdir(exp_root):
				d = os.path.join(exp_root, name)
				if not os.path.isdir(d):
					continue
				for f in os.listdir(d):
					if f.startswith("ans.") and f.endswith(".json"):
						found.add(f[4:-5].lower())
		except OSError:
			pass
		# Bahasa default selalu ada - kalau English, sudah masuk di atas.
		found.add(nxs_lang.normalize(DefLANG, default="en"))
		return sorted(found)

	def _available_langs(self):
		"""Kode -> nama bahasa, hanya yang benar-benar ada lokalnya."""
		codes = self._codes()
		return [(c, nxs_lang.describe(c)) for c in codes]

	def _effective(self, source):
		"""Bahasa yang benar-benar dipakai untuk reply ke user ini.

		getLang() sudahimplementasikan urutan prioritas (pilihan manual >
		tag presence > DefLANG), jadi jangan query database dua kali di
		sini - cukup andalkan hasilnya.
		"""
		try:
			return nxs_lang.normalize(getLang((source[1], source[1], source[2])),
			                           default=DefLANG.lower())
		except Exception:
			return DefLANG.lower()

	def _alias_hint(self):
		return ", ".join(sorted("%s=%s" % (k, v) for k, v in nxs_lang.ALIASES.items()))

	# ── command ────────────────────────────────────────────────

	def command_lang(self, stype, source, body, disp):
		if stype not in (sBase[0], sBase[1]):
			return None

		arg = (body or "").strip().split()
		arg = arg[0].lower() if arg else ""

		# ── tanpa argumen: tampilkan status ──
		if not arg:
			avail = self._available_langs()
			eff = self._effective(source)
			chosen = _get_user_lang(source[1], source[2])
			if chosen:
				mode = "\U0001f4cc dipilih manual"
			else:
				mode = "\U0001f4cc otomatis (dari client lo)"
			used = ", ".join(c for c, _ in avail)
			names = self._alias_hint() or ", ".join(n for _, n in avail)
			return Answer(self.AnsBase[0] % (
				nxs_lang.describe(eff), mode, used, names), stype, source, disp)

		# ── :lang list ──
		if arg == "list":
			if nxs_userlang is None:
				return Answer(self.AnsBase[7], stype, source, disp)
			rows = nxs_userlang.users_in_chat(source[1])
			if not rows:
				return Answer(self.AnsBase[6], stype, source, disp)
			lines = []
			for nick, lang in rows:
				if not lang or lang == "auto":
					lines.append("  \U0001f50d %s \u2014 otomatis" % nick)
				else:
					lines.append("  \U0001f4cc %s \u2014 %s"
					             % (nick, nxs_lang.describe(lang)))
			return Answer(self.AnsBase[5] % "\n".join(lines), stype, source, disp)

		# ── :lang auto \u2014 kembali ke deteksi presence ──
		if arg == "auto":
			if nxs_userlang is None:
				return Answer(self.AnsBase[7], stype, source, disp)
			if not nxs_userlang.clear_user_lang(source[1], source[2]):
				return Answer(self.AnsBase[3], stype, source, disp)
			# Sampe sini baruh yang aktif untuk pesan berikutnya.
			_set_reply_lang(source[1], source[2])
			return Answer(self.AnsBase[4], stype, source, disp)

		# ── :lang <code> ──
		code = nxs_lang.normalize(arg)
		if not nxs_lang.is_known(code):
			avail = self._available_langs()
			return Answer(self.AnsBase[2] % (
				arg, ", ".join(c for c, _ in avail)), stype, source, disp)

		if nxs_userlang is None:
			return Answer(self.AnsBase[7], stype, source, disp)

		ok, stored = nxs_userlang.set_user_lang(source[1], source[2], code)
		if not ok:
			return Answer(self.AnsBase[3], stype, source, disp)

		# Reply ini sendiri harus pakai bahasa BARU - paksa sekarang,
		# jangan tunggu pesan berikutnya.
		LocalizationContext.set(stored)
		return Answer(self.AnsBase[1] % nxs_lang.describe(stored),
		              stype, source, disp)

	# Setiap user boleh pilih bahasa sendiri - ini pengaturan per-user,
	# bukan aksi yang berbahaya. Access 1 cukup.
	commands = ((command_lang, "lang", 1,),)
