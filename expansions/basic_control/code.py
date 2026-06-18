# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "basic_control" # /code.py v.x14
#  Id: 06~8c
#  Original © (2009-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	def Check(self, conf):
		numb = 0
		while conf in Chats:
			if Chats[conf].IamHere is not None:
				break
			sleep(0.4)
			numb += 1
			if numb >= 50:
				break

	# Fix: raw string untuk regex agar \s valid di Python 3
	compile_chat = compile__(r"^[^\s'\"@<>&]+?@(?:conference|muc|conf|chat|group)\.[\w-]+?\.[\.\w-]+?$")

	AnsBase = (
		"[join] %s (%s) requested joining %s",           # 0
		" (reason: %s)",                                  # 1
		"Joined %s successfully.",                        # 2
		"Failed to join %s.",                             # 3
		"Done.",                                          # 4  (generic ok)
		"Already in that room.",                          # 5
		"Invalid room JID: %s",                           # 6
		"Hello! I am %s, invited by %s.",                 # 7
		"Leaving by request of %s.",                      # 8
		"Left %s.",                                       # 8 (leave answer)  -- idx 9
		"Left %s.",                                       # 10
		"Reloading by request of %s...",                  # 11
		"Shutting down by request of %s...",              # 12
		" (reconnect timer active)",                      # 13
		"Dispatcher offline.",                            # 14
		"Cannot create directory for %s.",                # 15
		"Dispatcher thread error.",                       # 16
		"Unknown dispatcher: %s",                         # 17
	)

	def command_join(self, stype, source, body, disp):
		if body:
			ls   = body.split()
			conf = ls.pop(0).lower()
			if self.compile_chat.match(conf):
				if conf not in Chats:
					confname = dynamic % conf
					if not os.path.exists(confname):
						try:
							os.makedirs(confname, 0o755)   # Fix: 0755 → 0o755
						except Exception:
							confname = None
					if confname:
						codename, disp_, cPref, nick = None, None, None, DefNick
						while ls:
							x = ls.pop()
							if x.startswith("1="):
								parts = x.split("1=", 1)
								if len(parts) == 2 and parts[1]:
									val = parts[1].lower()
									if val in Clients:          # Fix: has_key → in
										disp_ = val
							elif x.startswith("2="):
								parts = x.split("2=", 1)
								if len(parts) == 2 and parts[1]:
									if len(parts[1]) <= 16:
										nick = parts[1]
							elif x.startswith("3="):
								parts = x.split("3=", 1)
								if len(parts) == 2 and parts[1]:
									if parts[1] in cPrefs:
										cPref = parts[1]
							elif x.startswith("4="):
								parts = x.split("4=", 1)
								if len(parts) == 2 and parts[1]:
									codename = parts[1]
						inst = get_source(source[1], source[2])
						if GodName != inst:
							delivery(self.AnsBase[0] % (source[2], inst, conf))
						if not disp_:
							disp_ = IdleClient()
						Chats[conf] = sConf(conf, disp_, codename, cPref, nick)
						Chats[conf].load_all()
						Chats[conf].join()
						self.Check(conf)
						if conf in Chats and Chats[conf].IamHere:   # Fix: has_key → in
							Message(conf, self.AnsBase[7] % (ProdName, source[2]), disp_)
							answer = self.AnsBase[2] % conf
						else:
							answer = self.AnsBase[3] % conf
					else:
						answer = self.AnsBase[15] % conf
				else:
					answer = self.AnsBase[5]
			else:
				answer = self.AnsBase[6] % conf
		else:
			answer = self.AnsBase[4]
		Answer(answer, stype, source, disp)

	def command_rejoin(self, stype, source, body, disp):
		if body:
			conf = body.split()[0].lower()
		else:
			conf = source[1]
		if conf in Chats:                                   # Fix: has_key → in
			if online(Chats[conf].disp):
				Chats[conf].leave(self.AnsBase[8] % source[2])
				sleep(2)
				Chats[conf].join()
				self.Check(conf)
				if conf in Chats and Chats[conf].IamHere:
					answer = self.AnsBase[4]
				else:
					answer = self.AnsBase[3] % conf
			else:
				answer = self.AnsBase[14]
		else:
			answer = self.AnsBase[6] % conf
		Answer(answer, stype, source, disp)

	def command_leave(self, stype, source, body, disp):
		answer = None
		if body:
			conf = body.split()[0].lower()
		else:
			conf = source[1]
		if not body or enough_access(source[1], source[2], 7) or conf == source[1]:
			if conf in Chats:                               # Fix: has_key → in
				source_ = get_source(source[1], source[2])
				if GodName != source_:
					delivery(self.AnsBase[0] % (source[2], source_, conf))
				info = self.AnsBase[8] % source[2]
				Message(conf, info, Chats[conf].disp)
				sleep(2)
				Chats[conf].full_leave(info)
				if conf != source[1]:
					answer = self.AnsBase[9] % conf
			else:
				answer = self.AnsBase[6] % conf
		else:
			answer = "Access denied."
		if answer:                                          # Fix: locals().has_key → if answer
			Answer(answer, stype, source, disp)

	def command_reconnect(self, stype, source, body, disp):
		if body:
			Name = body.split()[0].lower()
		else:
			Name = get_disp(disp)
		if Name in InstancesDesc:                           # Fix: has_key → in
			if Name in Clients:                             # Fix: has_key → in
				if online(Name):
					try:
						client = Clients[Name]
						loop   = getattr(client, "_loop", None)
						if loop and loop.is_running():
							# slixmpp: disconnect() adalah coroutine
							# schedule_coro sudah handle asyncio.run_coroutine_threadsafe
							client.nx_disconnect()
							sleep(2)
					except IOError:
						pass
			if connect_client(Name, InstancesDesc[Name])[0]:
				for conf in Chats.values():                 # Fix: itervalues → values
					if Name == conf.disp:
						conf.join()
				answer = self.AnsBase[4]
			else:
				answer = self.AnsBase[3] % Name
		else:
			answer = self.AnsBase[17] % Name
		Answer(answer, stype, source, disp)

	def command_reload(self, stype, source, body, disp):
		exit_desclr = self.AnsBase[11] % source[2]
		# Fix: "тихо".decode("utf-8") → literal string (Python 3 str is unicode)
		if body.lower() not in ("-s", "silent", "тихо"):
			if body:
				exit_desclr += self.AnsBase[1] % body
			for conf in Chats.values():                     # Fix: itervalues → values
				Message(conf.name, exit_desclr, conf.disp)
		sleep(6)
		sys_exit("Reload command by %s" % source[2])

	def command_exit(self, stype, source, body, disp):
		exit_desclr = self.AnsBase[12] % source[2]
		if body.lower() not in ("-s", "silent", "тихо"):   # Fix: decode → literal
			if body:
				exit_desclr += self.AnsBase[1] % body
			for conf in Chats.values():                     # Fix: itervalues → values
				Message(conf.name, exit_desclr, conf.disp)
		sleep(6)
		sys_exit("Exit command by %s" % source[2])

	commands = (
		(command_join,      "join",      7,),
		(command_rejoin,    "rejoin",    7,),
		(command_leave,     "leave",     6,),
		(command_reconnect, "reconnect", 8,),
		(command_reload,    "reload",    8,),
		(command_exit,      "exit",      8,),
	)