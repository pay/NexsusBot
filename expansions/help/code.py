# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "help" # /code.py v.x7
#  Id: 03~4c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

def _active_help_lang(answers=None):
	"""Language code for the active thread, or None when unknown.

	Help files are plain text rather than reply strings, so this reads the
	per-thread localization context directly instead of going through
	LocalizedAnswers.

	LocalizationContext menyimpan bahasa per-thread, tapi command
	dieksekusi di thread BARU (sThread), jadi context thread-local sudah
	hilang waktu command_help jalan. Yang benar adalah bahasa dari
	LocalizedAnswers yang dipakai: instance-nya shared dan di-update
	setiap kali context dipasang, jadi masih berisi bahasa user yang
	benar. Thread-local dipakai sebagai fallback.
	"""
	lang = None
	try:
		from nxs_l10n import LocalizationContext
		lang = LocalizationContext.get_explicit()
	except Exception:
		lang = None
	if answers is not None:
		# `current_lang()` pakai bahasa thread pemanggil dulu, baru
		# fallback ke bahasa shared. `_lang` alone bisa milik user lain
		# yang command-nya jalan paralel.
		try:
			shared = answers.current_lang()
		except Exception:
			shared = getattr(answers, "_lang", None)
		if shared:
			lang = shared
	return lang.lower() if lang else None


class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	# Penanda baris di help. "*/cmd" (contoh perintah) pakai BULLET,
	# baris sisanya (catatan, sub-item) pakai DASH dengan indentasi.
	BULLET = "▸ "
	DASH   = "  • "
	# Lebar wrap untuk deskripsi panjang (XMPP client ~= 72 kolom).
	WIDTH  = 72

	def _wrap(self, text, prefix):
		"""Bungkus teks panjang; baris pertama diawali prefix, sisanya
		disejajarkan di bawah teks (bukan di bawah prefix)."""
		try:
			import textwrap
		except ImportError:
			return [prefix + text]
		avail = self.WIDTH - len(prefix)
		if avail < 20:
			avail = 20
		lines = textwrap.wrap(text, width=avail,
		                      initial_indent="", subsequent_indent="",
		                      break_long_words=False,
		                      break_on_hyphens=False)
		if not lines:
			return [prefix.rstrip()]
		cont = " " * (len(prefix) + 1)
		return [prefix + lines[0]] + [cont + l for l in lines[1:]]

	AnsBase = (
		"\u2139\ufe0f '%s' comes from expansion: %s",   # 0
		"\u2139\ufe0f '%s' needs access: %d",     # 1
		"%s\n%s",                                # 2  help header
		"\U0001f4d6 Usage:",                                # 3
		"\u274c No help file found.",                   # 4
		"\U0001f4cb Full list — use 'commands'.",       # 5
		"\U0001f4cb Commands (prefix '%s'):",               # 6
		"'%s'",                                  # 7  prefix display
		"\n\U0001f451 [8/God+] (%d): %s",                  # 8
		"\n\U0001f9d1 [7/Chief] (%d): %s",                 # 9
		"\n\U0001f48e [6] (%d): %s",                        # 10
		"\n\U0001f5e2 [5] (%d): %s",                        # 11
		"\n\U0001f528 [4] (%d): %s",                        # 12
		"\n\U0001f464 [3] (%d): %s",                        # 13
		"\n\u2696 [2] (%d): %s",                        # 14
		"\n\u2705 [1/All] (%d): %s",                    # 15
		"\nYour access: %s",                     # 16
		"\u274c Help file format error.",               # 17
	)

	def command_location(self, stype, source, body, disp):
		if body:
			command = body.lower()
			if command in Cmds:                  # Fix: has_key → in
				answer = self.AnsBase[0] % (command, Cmds[command].exp.name.upper())
			else:
				answer = "Unknown command."
		else:
			answer = "Provide a command name."
		Answer(answer, stype, source, disp)

	def command_comacc(self, stype, source, body, disp):
		if body:
			command = body.lower()
			if command in Cmds:                  # Fix: has_key → in
				answer = self.AnsBase[1] % (command, Cmds[command].access)
			else:
				answer = "Unknown command."
		else:
			answer = "Provide a command name."
		Answer(answer, stype, source, disp)

	mark = "{command}"

	def command_help(self, stype, source, body, disp):
		if not body:
			return Answer(self.AnsBase[5], stype, source, disp)
		parts   = body.split(None, 1)
		command = parts.pop(0).lower()
		if command not in Cmds:                  # Fix: has_key → in
			return Answer(gAnsBase[6], stype, source, disp)
		# Help ikut gate yang sama dengan dispatcher (Cmd.execute): kalau
		# peminta kurang akses, usage dan isi help tidak boleh bocor.
		if not enough_access(source[1], source[2], Cmds[command].access):
			return Answer(self.AnsBase[1] % (command, Cmds[command].access),
			              stype, source, disp)
		if parts:
			# Explicit :help <cmd> <lang> - user asked for a specific language.
			lang = parts.pop(0).lower()
			if len(lang) == 2 and lang.isalpha():
				helpf = os.path.join(ExpsDir, Cmds[command].exp.name,
				                     "%s.%s" % (Cmds[command].default, lang))
			else:
				helpf = None
		else:
			# No language given: resolve against the ACTIVE language of this user.
			# Previously this reused Cmds[command].help, which command_handler()
			# resolved ONCE at boot from DefLANG. Because :lang can change per user
			# at runtime, ":lang ru" still printed English help for everyone.
			exp_name  = Cmds[command].exp.name
			help_base = Cmds[command].default
			helpf     = None
			for cand in (_active_help_lang(self.AnsBase), "en"):
				if not cand:
					continue
				probe = os.path.join(ExpsDir, exp_name, "%s.%s" % (help_base, cand))
				if os.path.isfile(probe):
					helpf = probe
					break
			if helpf is None:
				helpf = Cmds[command].help
		if helpf and os.path.isfile(helpf):
			text = get_file(helpf)
			if self.mark in text:
				text  = text.format(command=command)
				lines = text.splitlines()
				if len(lines) >= 2:
					head = lines.pop(0)
					usage = lines.pop(0)
					ls = []
					for hl in self._wrap(head, ""):
						ls.append(hl)
					for ul in self._wrap(usage, ""):
						ls.append(ul)
					ls = [self.AnsBase[2] % (ls[0], ls[1])] + ls[2:] \
						if len(ls) >= 2 else [self.AnsBase[2] % (head, usage)]
					if lines:
						ls.append(self.AnsBase[3])
						for line in lines:
							line = line.strip()
							if not line:
								# Baris kosong: jangan jadi bullet kosong.
								ls.append("")
								continue
							if line.startswith("*/"):
								# "*/cmd" = contoh perintah (kebanyakan).
								# "*/ Catatan: ..." = catatan; di file help yang
								# ada, catatan selalu diawali huruf kapital.
								rest = line[2:].strip()
								Char = (self.DASH if rest[:1].isupper()
								        else self.BULLET)
								ls.extend(self._wrap(rest, Char))
							else:
								ls.extend(self._wrap(line, self.DASH))
					answer = "\n".join(ls)
				else:
					# File 2 baris saja (deskripsi + usage) tanpa daftar
					# contoh - tetap help yang valid, bukan error format.
					answer = "\n".join(ls)
			else:
				answer = self.AnsBase[17]
		else:
			answer = self.AnsBase[4]
		Answer(answer, stype, source, disp)

	def command_commands(self, stype, source, body, disp):
		# Fix: has_key → in, xrange → range, itervalues → values, itypes.Number() → dict counter
		pref   = (self.AnsBase[7] % Chats[source[1]].cPref
		          if (source[1] in Chats and Chats[source[1]].cPref)
		          else ":")
		answer = self.AnsBase[6] % pref
		cmds   = {}
		# Group command by access level, sorted.
		for cmd in Cmds.keys():
			if not Cmds[cmd].isAvailable:
				continue
			cmds.setdefault(Cmds[cmd].access, []).append(cmd)
		for ls in cmds.values():
			ls.sort()

		# Tampilkan HANYA command yang boleh dipakai oleh peminta: semua
		# command dengan access <= access peminta.  Grouping per level tetap
		# dipakai supaya jelas mana yang butuh level berapa, tapi angka dan
		# daftar harus COCOK — dulu lcmds[level] menghitung kumulatif
		# sementara cmds[level] hanya isinya yang persis di level itu, jadi
		# "N commands" tidak sesuai dengan nama yang dicetak.
		access = get_access(source[1], source[2])
		shown  = {l: sorted(c for c in cmds.get(l, []) if l <= access)
		          for l in range(1, 9)}
		shown  = {l: v for l, v in shown.items() if v}

		fmt_by_level = {8: 8, 7: 9, 6: 10, 5: 11,
		                 4: 12, 3: 13, 2: 14, 1: 15}
		for level in range(8, 0, -1):
			if level in shown:
				answer += self.AnsBase[fmt_by_level[level]] % (
				    len(shown[level]), ", ".join(shown[level]))

		if access > 8:
			access_str = "%d (Gandalf)" % access
		elif access == 8:
			access_str = "8 (God)"
		elif access == 7:
			access_str = "7 (Chief)"
		else:
			access_str = str(access)
		answer += self.AnsBase[16] % access_str
		if stype == sBase[1]:
			Answer(gAnsBase[11], stype, source, disp)
		Message(source[0], answer, disp)

	commands = (
		(command_location, "location", 1,),
		(command_comacc,   "comacc",   1,),
		(command_help,     "help",     1, False),
		(command_commands, "commands", 1, False),
	)