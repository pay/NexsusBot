# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "sconf_attrs" # /code.py v.x4
#  Id: 07~3c
#  Original © (2010-2011) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AnsBase = (
		"'%s' is offline.",                     # 0
		"Already using '%s'.",                  # 1
		"Unknown dispatcher: '%s'.",            # 2
		"Rejoining...",                         # 3
		"Nick set to: %s",                      # 4
		"Nick too long (max 16).",              # 5
		"Prefix removed.",                      # 6
		"No prefix set.",                       # 7
		"Prefix set to: '%s'",                  # 8
		"Prefix '%s' already set.",             # 9
		"Available prefixes: '%s'",             # 10
		"Current prefix: '%s'",                 # 11
		"No prefix.",                           # 12
		"Unknown state: '%s'",                  # 13
	)

	def command_redisp(self, stype, source, body, disp):
		parts = body.split() if body else []
		if parts:
			disp_ = parts.pop(0).lower()
			if disp_ in Clients:                        # Fix: has_key → in
				conf = parts.pop(0).lower() if parts else source[1]
				if conf in Chats:                       # Fix: has_key → in
					if Chats[conf].disp != disp_:
						if online(disp_):
							Chats[conf].leave(self.AnsBase[3])
							Chats[conf].disp = disp_
							Chats[conf].save()
							sleep(0.6)
							Chats[conf].join()
							if conf == source[1]:
								disp = disp_
							answer = "Done."
						else:
							answer = self.AnsBase[0] % disp_
					else:
						answer = self.AnsBase[1] % disp_
				else:
					answer = "Not in that room."
			else:
				answer = self.AnsBase[2] % disp_
		else:
			answer = "Usage: botjid <dispatcher> [room]"
		Answer(answer, stype, source, disp)

	def command_botnick(self, stype, source, body, disp):
		if source[1] not in Chats:             # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		if body:
			# Fix: xmpp.XMLescape() → tidak ada, cukup strip karakter berbahaya
			Nick = body.replace(chr(32), chr(95)).replace(chr(10), "").replace(chr(13), "").replace(chr(9), "").strip()
			if len(Nick) <= 16:
				Chats[source[1]].nick = Nick
				Chats[source[1]].save()
				Chats[source[1]].join()
				answer = self.AnsBase[4] % Nick
			else:
				answer = self.AnsBase[5]
		else:
			answer = "Current nick: %s" % Chats[source[1]].nick
		Answer(answer, stype, source, disp)

	def command_prefix(self, stype, source, body, disp):
		if source[1] not in Chats:             # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		if body:
			if enough_access(source[1], source[2], 6):
				body = body.lower()
				# Fix: "убрать".decode("utf-8") → literal
				if body in ("del", "убрать"):
					if Chats[source[1]].cPref:
						Chats[source[1]].cPref = None
						Chats[source[1]].save()
						answer = self.AnsBase[6]
					else:
						answer = self.AnsBase[7]
				elif body in cPrefs:
					if Chats[source[1]].cPref != body:
						Chats[source[1]].cPref = body
						Chats[source[1]].save()
						answer = self.AnsBase[8] % body
					else:
						answer = self.AnsBase[9] % body
				else:
					answer = self.AnsBase[10] % "', '".join(cPrefs)
			else:
				answer = "Access denied."
		elif Chats[source[1]].cPref:
			answer = self.AnsBase[11] % Chats[source[1]].cPref
		else:
			answer = self.AnsBase[12]
		Answer(answer, stype, source, disp)

	# Fix: all .decode("utf-8") → literal strings
	StatusDesc = {"чат": 0, "ушел": 1, "нет": 2, "занят": 3}

	ChatStatus = "status.db"

	def command_status(self, stype, source, body, disp):
		if not body:
			return Answer("Usage: botstatus <room|here|everywhere> <state> <text>", stype, source, disp)
		parts = body.split(None, 2)
		if len(parts) == 3:
			state  = parts.pop(1).lower()
			state  = sList[self.StatusDesc[state]] if state in self.StatusDesc else state
			if state in sList:
				chat, status = parts
				body_   = "%s|%s" % (state, status)
				chat    = chat.lower()
				# Fix: "везде".decode() → literal, itervalues → values
				if chat in ("everywhere", "везде"):
					for conf in Chats.values():
						conf.change_status(state, status)
						cat_file(chat_file(conf.name, self.ChatStatus), body_)
					answer = "Done."
				elif chat in ("here", "здесь"):
					if source[1] in Chats:
						Chats[source[1]].change_status(state, status)
						cat_file(chat_file(source[1], self.ChatStatus), body_)
						answer = "Done."
					else:
						answer = "Not in a room."
				elif chat in Chats:
					Chats[chat].change_status(state, status)
					cat_file(chat_file(chat, self.ChatStatus), body_)
					answer = "Done."
				else:
					answer = "Room not found."
			else:
				answer = self.AnsBase[13] % state
		else:
			answer = "Usage: botstatus <room|here|everywhere> <state> <text>"
		Answer(answer, stype, source, disp)

	def command_password(self, stype, source, body, disp):
		if source[1] not in Chats:             # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		if body:
			# Fix: "нет".decode() → literal
			if body in ("none", "нет"):
				body = None
			Chats[source[1]].code = body
			Chats[source[1]].save()
			answer = "Done."
		else:
			answer = str(Chats[source[1]].code)
		Answer(answer, stype, source, disp)

	def load_status(self, conf):
		filename = chat_file(conf, self.ChatStatus)
		if initialize_file(filename, "%s|%s" % (sList[0], DefStatus)):
			Chats[conf].set_status(*get_file(filename).split("|", 1))

	commands = (
		(command_redisp,   "botjid",     7,),
		(command_botnick,  "botnick",    6,),
		(command_status,   "botstatus",  7,),
		(command_password, "password",   6,),
		(command_prefix,   "prefix",     1, False),
	)

	handlers = ((load_status, "01si"),)