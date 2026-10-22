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
		"\U0001f4cb Current language: %s\n\U0001f4c4 Using: %s\n\U0001f50d Codes: %s\n\U0001f4a1 Aliases you can use: %s",  # 0
		"\u2705 Your language is now: %s.",                                                      # 1
		"\u274c Unknown language code: %s.\n\U0001f50d Codes: %s",                       # 2
		"\u274c Could not save your language choice.",                                                # 3
		"\u2139\ufe0f Back to auto-detection — ':lang auto' makes the bot read the <lang> tag from your client again.",       # 4
		"\U0001f4cb Languages in this room:\n%s",                                                  # 5
		"\u2139\ufe0f Nobody here has picked a language yet.",                                  # 6
		"\u274c Could not read the language database.",                                                 # 7
		"\U0001f4cc picked manually",                                                              # 8
		"\U0001f4cc automatic (from your client)",                                                 # 9
		"  \U0001f50d %s — automatic",                                                        # 10
	)

	# ── helpers ────────────────────────────────────────────────

	def _codes(self):
		"""Kode bahasa yang benar-benar ada teksnya, bukan cuma 'dikenal'.

		KNOWN di nxs_lang masih berisi 'ru'/'fi' karena ada file help-nya,
		tapi belum ada file locale reply - memilih salah satu cuma
		menghasilkan bahasa Inggris.  Bot tidak boleh menawarkan bahasa
		yang tidak bisa dilayani.
		"""
		return nxs_lang.languages_with_reply(ExpsDir)

	def _available_langs(self):
		"""(kode, nama) untuk setiap bahasa yang bisa dilayani."""
		codes = self._codes()
		return [(c, nxs_lang.describe(c)) for c in codes
		        if nxs_lang.is_known(c, ExpsDir)]

	def _effective(self, source):
		"""Bahasa yang benar-benar dipakai untuk reply ke user ini.

		getLang() sudah mengimplementasikan urutan prioritas (pilihan manual >
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
				mode = self.AnsBase[8]
			else:
				mode = self.AnsBase[9]
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
					lines.append(self.AnsBase[10] % nick)
				else:
					lines.append("  \U0001f4cc %s — %s"
					             % (nick, nxs_lang.describe(lang)))
			return Answer(self.AnsBase[5] % "\n".join(lines), stype, source, disp)

		# ── :lang auto \u2014 kembali ke deteksi presence ──
		if arg == "auto":
			if nxs_userlang is None:
				return Answer(self.AnsBase[7], stype, source, disp)
			if not nxs_userlang.clear_user_lang(source[1], source[2]):
				return Answer(self.AnsBase[3], stype, source, disp)
			# Sampe sini baru yang aktif untuk pesan berikutnya.
			_set_reply_lang(source[1], source[2])
			return Answer(self.AnsBase[4], stype, source, disp)

		# ── :lang <code> ──
		code = nxs_lang.normalize(arg)
		if not nxs_lang.is_known(code, ExpsDir):
			avail = self._available_langs()
			return Answer(self.AnsBase[2] % (
				arg, ", ".join(c for c, _ in avail)), stype, source, disp)

		if nxs_userlang is None:
			return Answer(self.AnsBase[7], stype, source, disp)

		ok, stored = nxs_userlang.set_user_lang(source[1], source[2], code, ExpsDir)
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
