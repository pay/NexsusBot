# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "info" # /code.py v.x8
#  Id: 11~7c
#  Original © (2010-2012) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AnsBase = (
		"Today's visitors (%s):\n%s\n(online: %s)",   # 0
		"No visitors today.",                           # 1
		"List (%s):\n%s",                              # 2
		"Offline (%s):\n%s\n(online: %s)",             # 3
		"No offline users.",                            # 4
		"Rooms:",                                       # 5
		"No rooms.",                                    # 6
		"Dispatchers:",                                 # 7
		"Online:",                                      # 8
		"Search results (%s):\n%s",                    # 9
		"Not found.",                                   # 10
	)

	def command_online(self, stype, source, body, disp):
		# Fix: ithr.getNames() → list thread names via threading
		thr_names = [t.name for t in threading.enumerate()]
		ls = self.AnsBase[7]
		for numb, disp_ in enumerate(sorted(InstancesDesc.keys()), 1):
			alive   = str("%s-%s" % (sBase[13], disp_) in thr_names)
			connect = str(online(disp_))
			ls += "\n%d) %s - %s - %s" % (numb, disp_, connect, alive)
		if stype == sBase[1]:
			Answer("Sent to PM.", stype, source, disp)
		Message(source[0], ls, disp)

	def command_chatslist(self, stype, source, body, disp):
		ls     = []
		numb   = 0
		access = enough_access(source[1], source[2], 7)
		for conf_str, conf in sorted(Chats.items()):
			numb  += 1
			arole  = getattr(conf.get_user(conf.nick), "role", None)
			cName  = conf_str.split("@")[0]
			disp_  = (conf.disp if access else "***")
			cPref  = str(conf.cPref)
			# Fix: itypes.Number() → simple counter
			online_count = sum(1 for u in conf.get_users() if u.ishere)
			role_str = ("%s/%s" % arole) if arole else str(arole)
			ls.append('%d) %s/%s [%s] "%s" (%d) - %s' % (
				numb, cName, conf.nick, disp_, cPref, online_count, role_str))
		if ls:
			if stype == sBase[1]:
				Answer("Sent to PM.", stype, source, disp)
			ls.insert(0, self.AnsBase[5])
			Message(source[0], "\n".join(ls), disp)
		else:
			Answer(self.AnsBase[6], stype, source, disp)

	def command_inmuc(self, stype, source, body, disp):
		if source[1] not in Chats:                     # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		ls     = self.AnsBase[8]
		numb   = 0
		access = enough_access(source[1], source[2], 4)
		owners, admins, members, none = [], [], [], []
		for user in Chats[source[1]].sorted_users():
			if not user.ishere:
				continue
			data = "%s [%d]" % (user.nick, get_access(source[1], user.nick))
			if access and user.source:
				data += " (%s)" % user.source
			aff = user.role[0]
			if aff == aRoles[5]:
				owners.append(data)
			elif aff == aRoles[4]:
				admins.append(data)
			elif aff == aRoles[3]:
				members.append(data)
			else:
				none.append(data)
		for label, group in (("Owners", owners), ("Admins", admins),
		                     ("Members", members), ("Others", none)):
			if group:
				ls += "\n\n%s:" % label
				for x in group:
					numb += 1
					ls += "\n%d) %s" % (numb, x)
		if stype == sBase[1]:
			Answer("Sent to PM.", stype, source, disp)
		Message(source[0], ls, disp)

	def command_visitors(self, stype, source, body, disp):
		answer = None
		if source[1] not in Chats:                     # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		cmd = body.lower() if body else ""
		# Fix: "сегодня".decode("utf-8") → literal string
		if cmd in ("today", "сегодня"):
			offline, online_count = [], 0
			date = Yday()
			for user in Chats[source[1]].sorted_users():
				if not user.ishere:
					if user.date[1] == date:
						if user.source:
							offline.append("%d. %s (%s)" % (len(offline)+1, user.nick, user.source))
						else:
							offline.append("%d. %s" % (len(offline)+1, user.nick))
				else:
					online_count += 1
			if offline:
				if stype == sBase[1]:
					answer = "Sent to PM."
				Message(source[0], self.AnsBase[0] % (len(offline), "\n".join(offline), online_count), disp)
			else:
				answer = self.AnsBase[1]
		elif cmd in ("dates", "даты"):                  # Fix: decode → literal
			lines = []
			for user in Chats[source[1]].sorted_users():
				lines.append("%d. %s\t\t%s" % (len(lines)+1, user.nick, user.date[2]))
			if stype == sBase[1]:
				answer = "Sent to PM."
			Message(source[0], self.AnsBase[2] % (len(lines), "\n".join(lines)), disp)
		elif cmd in ("roles", "роли"):                  # Fix: decode → literal
			offline, online_count = [], 0
			for user in Chats[source[1]].sorted_users():
				if not user.ishere:
					offline.append("%d. %s\t\t- %s" % (len(offline)+1, user.nick, "%s/%s" % user.role))
				else:
					online_count += 1
			if offline:
				if stype == sBase[1]:
					answer = "Sent to PM."
				Message(source[0], self.AnsBase[3] % (len(offline), "\n".join(offline), online_count), disp)
			else:
				answer = self.AnsBase[4]
		elif cmd in ("list", "лист"):                   # Fix: decode → literal
			nicks = sorted(Chats[source[1]].get_nicks())
			if stype == sBase[1]:
				answer = "Sent to PM."
			Message(source[0], self.AnsBase[2] % (len(nicks), ", ".join(nicks)), disp)
		else:
			offline, online_count = [], 0
			for user in Chats[source[1]].sorted_users():
				if not user.ishere:
					if user.source:
						offline.append("%d. %s (%s)" % (len(offline)+1, user.nick, user.source))
					else:
						offline.append("%d. %s" % (len(offline)+1, user.nick))
				else:
					online_count += 1
			if offline:
				if stype == sBase[1]:
					answer = "Sent to PM."
				Message(source[0], self.AnsBase[3] % (len(offline), "\n".join(offline), online_count), disp)
			else:
				answer = self.AnsBase[4]
		if answer:                                      # Fix: locals().has_key → if answer
			Answer(answer, stype, source, disp)

	# Fix: "string".decode("utf-8") → literal string
	CharsCY = "етуоранкхсвм"
	CharsLA = "etyopahkxcbm"
	eqMap   = tuple(zip("етуоранкхсвм", "etyopahkxcbm"))

	def _sub(self, text, eq):
		for a, b in eq:
			text = text.replace(a, b)
		return text

	def command_search(self, stype, source, body, disp):
		if not body:
			return Answer("No query.", stype, source, disp)
		answer = None
		ls     = []
		access = enough_access(source[1], source[2], 7)
		query  = self._sub(body.lower(), self.eqMap)
		for conf_str, conf in sorted(Chats.items()):
			for user in conf.sorted_users():
				if not user.ishere:
					continue
				nick_n = self._sub(user.nick.lower(), self.eqMap)
				src_n  = self._sub(user.source, self.eqMap) if user.source else ""
				if query in nick_n or (user.source and query in src_n):
					if user.source and access:
						ls.append("%d) %s (%s) [%s]" % (len(ls)+1, user.nick, conf_str, user.source))
					else:
						ls.append("%d) %s (%s)" % (len(ls)+1, user.nick, conf_str))
					if len(ls) >= 20:
						break
		if ls:
			if stype == sBase[1]:
				answer = "Sent to PM."
			Message(source[0], self.AnsBase[9] % (len(ls), "\n".join(ls)), disp)
		else:
			answer = self.AnsBase[10]
		if answer:                                      # Fix: locals().has_key → if answer
			Answer(answer, stype, source, disp)

	commands = (
		(command_online,    "online",    7,),
		(command_chatslist, "chatslist", 5,),
		(command_inmuc,     "inmuc",     2,),
		(command_visitors,  "visitors",  4,),
		(command_search,    "search",    2,),
	)