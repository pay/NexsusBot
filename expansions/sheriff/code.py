# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3 / slixmpp)
# exp_name = "sheriff" # /code.py v.x8
#  Id: 15~6c
#  Original © (2011-2012) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	GoodServers = [
		"jabber.ru", "xmpp.ru", "jabbers.ru", "xmpps.ru",
		"jabber.org", "xmpp.org", "gmail.com", "jabberon.ru",
		"talkonaut.com", "gajim.org", "jabbrik.ru", "qip.ru",
		"blackfishka.ru", "helldev.net", "ya.ru", "jabberworld.net",
		"conversations.im", "jabber.de", "404.city"
	]

	if DefLANG != "RU":
		GoodServers += ["jabber.com", "xmpp.com", "jabber.co.uk", "xmpp.co.uk"]

	LawsFile = "laws.db"

	Prison, Antiwipe = {}, {}

	# Fix: Obscene → simple regex for obvious spam/obscene patterns
	# (original Obscene was a pre-built word list, not available here)
	Obscene = compile__(
		r"(?i)\b(spam|fuck|shit|bitch|asshole|bastard|cunt|dick|cock|pussy"
		r"|хуй|пизд|блять|ёбан|сука|мудак|залупа|пидор|шлюх)\b"
	)

	AnsBase = (
		"",                                             # 0
		"",                                             # 1
		"",                                             # 2
		"",                                             # 3
		"Advertising is not allowed here.",             # 4
		"",                                             # 5
		"",                                             # 6
		"",                                             # 7
		"Obscene language is not allowed here.",        # 8
		"Presence/status is too long.",                 # 9
		"%s: Auto-banned after %d kicks.",              # 10
		"%s: You are devoiced, wait.",                  # 11
		"%s: Anti-wipe triggered.",                     # 12
		"Flood detected.",                              # 13
		"You are devoiced. Wait: %s",                   # 14
		"",                                             # 15
		"",                                             # 16
		"%s: Please verify yourself.",                  # 17
		"%s: Answer this question to join: %s",         # 18
		# questions format: "question|answer\nquestion2|answer2"
		"What is 2+2?|4\nWhat color is the sky?|blue",  # 19
		"",                                             # 20
		"",                                             # 21
		"",                                             # 22
		"",                                             # 23
		"\nAspace: ",                                   # 24
		"[ON]\n",                                       # 25
		"[OFF]\n",                                      # 26
		"Nick max len: %d\nAwipe: ",                    # 27
		"Auto-ban after: %d kicks\nVerif: ",            # 28
		"Loyalty: %d\nAtiser: ",                        # 29
		"Devoice time: %d sec\nAobscene: ",             # 30
		"Msg max len: %d\nAcaps: ",                     # 31
		"Presence max len: %d\nSPARTA: ",               # 32
		"",                                             # 33
		"Server already in list.",                      # 34
		"Server not in list.",                          # 35
		"Invalid server (must contain a dot).",         # 36
	)

	class Convict(object):
		def __init__(self):
			self.devoice  = 0
			self.prdates  = [time.time()]
			self.msdates  = []
			self.offenses = 0
			# Fix: itypes.Number() → AtomicNumber()
			self.kicks    = AtomicNumber()
			self.verif    = False
			self.vakey    = ""
			self.vnumb    = AtomicNumber()

		def autenticated(self):
			self.verif = True
			self.vakey = ""

		def leaved(self):
			self.msdates = []
			self.vakey   = ""

		def setDevoice(self):
			self.devoice = time.time()

		def getDevoice(self):
			return time.time() - self.devoice

		def addPrTime(self):
			self.prdates.append(time.time())

		def addMsTime(self):
			self.msdates.append(time.time())

	def command_order(self, stype, source, body, disp):

		def change_cfg(chat, opt, state):
			# Fix: decode → literal
			if state in ("on", "1", "вкл"):
				ChatsAttrs[chat]["laws"][opt] = True
				return "Done."
			elif state in ("off", "0", "выкл"):
				ChatsAttrs[chat]["laws"][opt] = False
				return "Done."
			return "Invalid state."

		def alt_change_cfg(chat, opt, state, drange):
			if isNumber(state):
				s = int(state)
				# Fix: xrange → range
				if s in range(*drange):
					ChatsAttrs[chat]["laws"][opt] = s
					return "Done."
				return "Out of range."
			return "Invalid number."

		if source[1] not in Chats:          # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)

		if not body:
			laws = ChatsAttrs[source[1]]["laws"]
			answer  = "\nAspace: "
			answer += self.AnsBase[25 if laws["space"] else 26][:-1]
			answer += self.AnsBase[27] % laws["lnick"]
			answer += self.AnsBase[25 if laws["awipe"] else 26]
			answer += self.AnsBase[28] % laws["aban"]
			answer += self.AnsBase[25 if laws["verif"] else 26]
			answer += self.AnsBase[29] % laws["loyalty"]
			answer += self.AnsBase[25 if laws["tiser"] else 26]
			answer += self.AnsBase[30] % laws["dtime"]
			answer += self.AnsBase[25 if laws["obscene"] else 26][:-1]
			answer += self.AnsBase[31] % laws["len"]
			answer += self.AnsBase[25 if laws["lower"] else 26][:-1]
			answer += self.AnsBase[32] % laws["prlen"]
			answer += self.AnsBase[25 if laws["sparta"] else 26][:-1]
			return Answer(answer, stype, source, disp)

		ls   = body.lower().split()
		arg0 = ls.pop(0)
		if ls:
			arg1 = ls.pop(0)
			cfg_map = {
				"awipe": ("awipe", None), "антивайп": ("awipe", None),
				"aspace": ("space", None), "антиспэйс": ("space", None),
				"sparta": ("sparta", None), "спарта": ("sparta", None),
				"verif": ("verif", None), "авторизация": ("verif", None),
				"atiser": ("tiser", None), "антиреклама": ("tiser", None),
				"aobscene": ("obscene", None), "антимат": ("obscene", None),
				"acaps": ("lower", None), "антикапс": ("lower", None),
			}
			alt_map = {
				"lnick": ("lnick", (12, 33)), "никлен": ("lnick", (12, 33)),
				"aban": ("aban", (2, 7)), "автобан": ("aban", (2, 7)),
				"loyalty": ("loyalty", (1, 6)), "лояльность": ("loyalty", (1, 6)),
				"devoice": ("dtime", (60, 361)), "девойс": ("dtime", (60, 361)),
				"msglen": ("len", (512, 2049)), "мсглен": ("len", (512, 2049)),
				"prslen": ("prlen", (128, 513)), "прзлен": ("prlen", (128, 513)),
			}
			if arg0 in ("servers", "сервера"):
				if ls:
					server = ls.pop(0)
					if "." in server:
						if arg1 in ("add", "+"):
							combined = self.GoodServers + ChatsAttrs[source[1]]["laws"]["list"]
							if server not in combined:
								ChatsAttrs[source[1]]["laws"]["list"].append(server)
								answer = "Done."
							else:
								answer = self.AnsBase[34]
						elif arg1 in ("del", "-"):
							if server in ChatsAttrs[source[1]]["laws"]["list"]:
								ChatsAttrs[source[1]]["laws"]["list"].remove(server)
								answer = "Done."
							else:
								answer = self.AnsBase[35]
						else:
							answer = "Invalid action."
					else:
						answer = self.AnsBase[36]
				else:
					answer = "Not enough arguments."
			elif arg0 in cfg_map:
				opt, _ = cfg_map[arg0]
				answer = change_cfg(source[1], opt, arg1)
			elif arg0 in alt_map:
				opt, drange = alt_map[arg0]
				answer = alt_change_cfg(source[1], opt, arg1, drange)
			else:
				answer = "Unknown option."
			if answer == "Done.":
				cat_file(chat_file(source[1], self.LawsFile),
				         str(ChatsAttrs[source[1]]["laws"]))
		elif arg0 in ("servers", "сервера"):
			answer = "\nDefault:\n%s" % enumerated_list(sorted(self.GoodServers))
			if ChatsAttrs[source[1]]["laws"]["list"]:
				answer += "\n\nDefined:\n%s" % enumerated_list(
					sorted(ChatsAttrs[source[1]]["laws"]["list"]))
		else:
			answer = "Invalid argument."
		Answer(answer, stype, source, disp)

	def special_kick(self, chat, nick, text):
		Chats[chat].kick(nick, "%s: %s" % (get_nick(chat), text))
		# Fix: ithr.ThrKill → raise SelfExc to stop thread
		raise SelfExc("sheriff_kick")

	def sheriffs_loyalty(self, chat):
		loy    = ChatsAttrs[chat]["laws"]["loyalty"]
		access = min(loy, 2)
		return (loy, access)

	# Fix: raw strings for regex
	compile_link = compile__(r"(?:https?|ftp|svn)://[^\s'\"<>]+", 64)
	compile_chat = compile__(r"[^\s]+?@(?:conference|muc|conf|chat|group)\.[\w-]+?\.[\w-]+", 64)

	def tiser_checker(self, body):
		body = body.lower()
		return bool(self.compile_link.search(body) or self.compile_chat.search(body))

	def lower_checker(self, chat, body):
		# Remove spaces, newlines and nicks before counting caps
		clean = body
		for ch in [chr(32), chr(10), chr(13), chr(9)]:
			clean = clean.replace(ch, "")
		for nick in Chats[chat].get_nicks():
			clean = clean.replace(nick, "")
		clean = clean.strip()
		numb  = sum(1 for c in clean if c.isupper())
		return numb > 12 and numb > (len(clean) / 3)

	obscene_checker = lambda self, body: self.Obscene.search(" " + body + " ")

	def check_nick(self, chat, nick):
		def nick_checker(chat, nick):
			if "%" in nick or "/" in nick:
				return True
			nick_low = nick.split()[0].lower() if nick.split() else ""
			if nick_low in Cmds:            # Fix: has_key → in
				return True
			lnick = ChatsAttrs[chat]["laws"]["lnick"]
			if lnick and len(nick) > lnick:
				return True
			return False

		if Chats[chat].isModer and ChatsAttrs[chat]["laws"].get("lnick"):
			if nick_checker(chat, nick):
				self.special_kick(chat, nick, "Invalid nick.")

	def awipeClear(self, chat, ls):
		for sUser in Chats[chat].get_users():
			if sUser.source in ls:
				if not sUser.ishere:
					if Chats[chat].isHere(sUser.nick):
						Chats[chat].desc.pop(sUser.nick, None)
					self.Prison[chat].pop(sUser.source, None)
		for source_ in ls:
			Chats[chat].none(source_)
			sleep(0.4)

	def get_server(self, source, state=False):
		if "@" in source:
			source = source.split("@")[1]
			if state:
				source = source.split(".", 1)[1] if "." in source else source
		return source

	def GoodServers__(self, chat):
		return self.GoodServers + ChatsAttrs[chat]["laws"]["list"] + [self.get_server(chat, True)]

	def check_wipe(self, chat, nick, role, inst):
		if role != aRoles[2]:
			return
		BsNick = get_nick(chat)
		if ChatsAttrs[chat]["laws"]["sparta"]:
			jid = self.get_server(inst)
			if jid not in self.GoodServers__(chat):
				Reason = "%s: This is SPARTA!!" % BsNick
				Chats[chat].outcast(jid, Reason)
				Chats[chat].kick(nick, Reason)
		elif ChatsAttrs[chat]["laws"]["awipe"]:
			Time = time.time()
			if (Time - Chats[chat].sdate) >= 60:
				diff = Time - self.Antiwipe[chat]["ltime"]
				if diff > 360 and self.Antiwipe[chat]["clear"]:
					sThread(self.awipeClear.__name__, self.awipeClear,
					        (chat, self.Antiwipe[chat]["clear"],))
				if diff > 15:
					self.Antiwipe[chat]["ltime"] = Time
					self.Antiwipe[chat]["jids"]  = [inst]
				else:
					self.Antiwipe[chat]["jids"].append(inst)
					joined = self.Antiwipe[chat]["jids"]
					Numb   = len(joined)
					if Numb >= 3:
						self.Antiwipe[chat]["ltime"] = Time
						jid = self.get_server(inst)
						if (jid == self.get_server(joined[-2]) and
						    jid == self.get_server(joined[-3])):
							if jid not in self.GoodServers__(chat):
								ls = [u for u in Chats[chat].get_users()
								      if u.source and u.ishere
								      and u.nick != BsNick
								      and u.role[0] == aRoles[2]
								      and jid == self.get_server(u.source)
								      and u.source in self.Prison[chat]
								      and not self.Prison[chat][u.source].verif]
								Chats[chat].outcast(jid, self.AnsBase[12] % BsNick)
								for u in ls:
									Chats[chat].kick(u.nick, self.AnsBase[12] % BsNick)
							else:
								for u in Chats[chat].get_users():
									if (u.source and u.ishere
									    and u.nick != BsNick
									    and u.role[0] == aRoles[2]
									    and jid == self.get_server(u.source)
									    and u.source in self.Prison[chat]
									    and not self.Prison[chat][u.source].verif):
										self.Antiwipe[chat]["clear"].append(u.source)
										Chats[chat].outcast(u.source, self.AnsBase[12] % BsNick)
						else:
							self.Antiwipe[chat]["clear"].append(inst)
							Chats[chat].outcast(inst, self.AnsBase[12] % BsNick)
						raise SelfExc("antiwipe_triggered")  # Fix: ithr.ThrKill

	Questions = []

	def sheriff_04eh(self, chat, nick, source_, role, stanza, disp):
		if not source_ or nick == get_nick(chat):
			return
		access = get_access(chat, nick)
		if access > self.sheriffs_loyalty(chat)[1]:
			return
		prisoner = self.Prison[chat].get(source_)
		if prisoner:
			prisoner.addPrTime()
			if prisoner.devoice:
				eTime = prisoner.getDevoice()
				dtime = ChatsAttrs[chat]["laws"]["dtime"]
				if eTime < dtime:
					Chats[chat].visitor(nick, self.AnsBase[11] % get_nick(chat))
					Message("%s/%s" % (chat, nick),
					        self.AnsBase[14] % Time2Text(dtime - eTime), disp)
				else:
					prisoner.devoice = 0
		else:
			self.Prison[chat][source_] = prisoner = self.Convict()

		if not prisoner.verif and access >= 2:
			prisoner.autenticated()

		self.check_wipe(chat, nick, role[0], source_)
		self.check_nick(chat, nick)

		if (ChatsAttrs[chat]["laws"]["verif"] and access < 2
		    and aRoles[2] == role[0] and not prisoner.verif
		    and not prisoner.devoice):
			Chats[chat].visitor(nick, self.AnsBase[17] % get_nick(chat))
			if not self.Questions:
				for qu in self.AnsBase[19].splitlines():
					if "|" in qu:
						q, a = qu.split("|", 1)
						self.Questions.append((q.strip(), a.strip().lower()))
			if self.Questions:
				qu, an = choice(self.Questions)
				prisoner.vakey = an
				Message("%s/%s" % (chat, nick), self.AnsBase[18] % (get_nick(chat), qu), disp)

		lst = prisoner.prdates
		if len(lst) >= 4:
			if (lst[-1] - lst[0]) <= 10:
				prisoner.prdates = [lst[-1]]
				self.special_kick(chat, nick, self.AnsBase[13])
			else:
				prisoner.prdates.pop(0)

		# Fix: stanza.getStatus() → slixmpp presence["status"]
		try:
			status = stanza.get("status", "") if hasattr(stanza, "get") else ""
		except Exception:
			status = ""
		if status:
			laws = ChatsAttrs[chat]["laws"]
			if laws["tiser"] and self.tiser_checker(status):
				self.special_kick(chat, nick, self.AnsBase[4])
			if laws["obscene"] and self.obscene_checker(status):
				self.special_kick(chat, nick, self.AnsBase[8])
			if laws["prlen"] and len(status) > laws["prlen"]:
				self.special_kick(chat, nick, self.AnsBase[9])

	def sheriff_05eh(self, chat, nick, sbody, scode, disp):
		if nick == get_nick(chat):
			return
		source_ = get_source(chat, nick)
		if not source_:
			return
		prisoner = self.Prison[chat].get(source_)
		if not prisoner:
			return
		if not Chats[chat].isModer or scode in (sCodes[0], sCodes[3]):
			del self.Prison[chat][source_]
		else:
			prisoner.leaved()
			if scode == sCodes[2]:
				kicks = prisoner.kicks.plus()
				aban  = ChatsAttrs[chat]["laws"]["aban"]
				if aban and kicks >= aban:
					del self.Prison[chat][source_]
					Chats[chat].outcast(source_,
					    self.AnsBase[10] % (get_nick(chat), aban))

	def sheriff_06eh(self, chat, old_nick, nick, disp):
		if nick == get_nick(chat) or not Chats[chat].isModer:
			return
		sUser = Chats[chat].get_user(nick)
		if not getattr(sUser, "source", None):
			return
		prisoner = self.Prison[chat].get(sUser.source)
		if not prisoner:
			return
		prisoner.addPrTime()
		self.check_wipe(chat, nick, sUser.role[0], sUser.source)
		self.check_nick(chat, nick)
		lst = prisoner.prdates
		if len(lst) >= 4:
			if (lst[-1] - lst[0]) <= 10:
				prisoner.prdates = [lst[-1]]
				self.special_kick(chat, nick, self.AnsBase[13])
			else:
				prisoner.prdates.pop(0)

	def sheriff_07eh(self, chat, nick, role, disp):
		if nick == get_nick(chat):
			return
		sUser = Chats[chat].get_user(nick)
		if not getattr(sUser, "source", None):
			return
		is_prisoner = sUser.access <= self.sheriffs_loyalty(chat)[1] and Chats[chat].isModer
		if sUser.source in self.Prison[chat]:
			if not is_prisoner:
				del self.Prison[chat][sUser.source]
		elif is_prisoner:
			self.Prison[chat][sUser.source] = self.Convict()

	def sheriff_08eh(self, chat, nick, stanza, disp):
		if nick == get_nick(chat) or not Chats[chat].isModer:
			return
		source_ = get_source(chat, nick)
		if not source_:
			return
		prisoner = self.Prison[chat].get(source_)
		if not prisoner:
			return
		prisoner.addPrTime()
		lst = prisoner.prdates
		if len(lst) >= 4:
			if (lst[-1] - lst[0]) <= 10:
				prisoner.prdates = [lst[-1]]
				self.special_kick(chat, nick, self.AnsBase[13])
			else:
				prisoner.prdates.pop(0)
		try:
			status = stanza.get("status", "") if hasattr(stanza, "get") else ""
		except Exception:
			status = ""
		if status:
			laws = ChatsAttrs[chat]["laws"]
			if laws["tiser"] and self.tiser_checker(status):
				self.special_kick(chat, nick, self.AnsBase[4])
			if laws["obscene"] and self.obscene_checker(status):
				self.special_kick(chat, nick, self.AnsBase[8])
			if laws["prlen"] and len(status) > laws["prlen"]:
				self.special_kick(chat, nick, self.AnsBase[9])

	def sheriff_01eh(self, stanza, isConf, stype, source, body, isToBs, disp):
		"""Handle messages — anti-spam, anti-obscene, anti-caps, anti-tiser."""
		if not isConf or not Chats[source[1]].isModer:
			return
		nick = source[2]
		if not nick or nick == get_nick(source[1]):
			return
		source_ = get_source(source[1], nick)
		if not source_:
			return
		prisoner = self.Prison[source[1]].get(source_)
		if not prisoner:
			return
		laws = ChatsAttrs[source[1]]["laws"]

		# Verify answer
		if prisoner.vakey and not prisoner.verif:
			if body.strip().lower() == prisoner.vakey:
				prisoner.autenticated()
				Chats[source[1]].participant(nick)
			else:
				self.special_kick(source[1], nick, "Wrong answer.")
			raise NodeProcessed()

		# Anti-tiser
		if laws["tiser"] and self.tiser_checker(body):
			prisoner.offenses += 1
			self.special_kick(source[1], nick, self.AnsBase[4])

		# Anti-obscene
		if laws["obscene"] and self.obscene_checker(body):
			prisoner.offenses += 1
			if not prisoner.devoice:
				prisoner.setDevoice()
				Chats[source[1]].visitor(nick, self.AnsBase[8])
				Message("%s/%s" % (source[1], nick),
				        self.AnsBase[14] % Time2Text(laws["dtime"]), disp)
			raise NodeProcessed()

		# Anti-caps
		if laws["lower"] and self.lower_checker(source[1], body):
			prisoner.offenses += 1
			self.special_kick(source[1], nick, "Caps lock is not allowed.")

		# Anti-space (single long word)
		if laws["space"] and body and " " not in body and len(body) > 64:
			prisoner.offenses += 1
			self.special_kick(source[1], nick, "No spaces detected (flood).")

		# Message length
		if laws["len"] and len(body) > laws["len"]:
			self.special_kick(source[1], nick, "Message too long.")

		prisoner.addMsTime()

	def sheriff_01si(self, chat):
		self.Prison[chat]   = {}
		self.Antiwipe[chat] = {"ltime": 0, "jids": [], "clear": []}
		desc = ChatsAttrs.setdefault(chat, {})
		desc["laws"] = {
			"awipe": True, "space": True, "verif": False,
			"tiser": True, "obscene": False, "lower": False,
			"sparta": False, "list": [], "dtime": 180,
			"loyalty": 1, "aban": 3, "prlen": 256, "lnick": 24, "len": 1024
		}
		filename = chat_file(chat, self.LawsFile)
		if initialize_file(filename, str(desc["laws"])):
			try:
				desc["laws"] = eval(get_file(filename))
			except Exception:
				pass

	def sheriff_04si(self, chat):
		self.Prison.pop(chat, None)
		self.Antiwipe.pop(chat, None)

	commands = ((command_order, "order", 6,),)

	handlers = (
		(sheriff_01si, "01si"),
		(sheriff_04si, "04si"),
		(sheriff_01eh, "01eh"),
		(sheriff_04eh, "04eh"),
		(sheriff_05eh, "05eh"),
		(sheriff_06eh, "06eh"),
		(sheriff_07eh, "07eh"),
		(sheriff_08eh, "08eh"),
	)