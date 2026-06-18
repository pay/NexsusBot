# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2
# exp_name = "config" # /code.py v.x10 — ported to Python 3
#  Code © (2011-2013) by WitcherGeralt [alkorgun@gmail.com]

class expansion_temp(expansion):

	AnsBase = (
		"Updated: %s",                        # 0
		"Nothing to update.",                 # 1
		"Current config:\n",                  # 2
		"No extra clients configured.",       # 3
		"Leaving rooms...",                   # 4
		"Disconnecting...",                   # 5
		"New primary dispatcher: %s",         # 6
		"Can't remove the only client.",      # 7
		"Thread error.",                      # 8
		"Connection failed.",                 # 9
		"Already connected.",                 # 10
		"Client not found: %s",              # 11
		"Client offline: %s",                # 12
	)

	def __init__(self, name):
		expansion.__init__(self, name)

	def get_config(self, config):
		cfg = []
		for s in config.sections():
			cfg.append("[%s]" % s.upper())
			for (opt, i) in config.items(s):
				cfg.append("%s = %s" % (opt.upper(), str(i)))
		return "\r\n".join(cfg)

	opts      = ("memory", "incoming", "chat", "private", "tls", "mserve", "getexc", "status", "resource")
	optsGlobEq = ("MaxMemory", "IncLimit", "ConfLimit", "PrivLimit", "ConTls", "Mserve", "GetExc", "DefStatus", "GenResource")

	def command_config(self, stype, source, body, disp):
		answer = None
		if body:
			ConfigDesc = {}
			for x in body.split():
				if "=" not in x:
					continue
				opt, data = x.split("=", 1)
				if not data:
					continue
				opt = opt.lower()
				for title in GenCon.sections():
					if opt in GenCon.options(title):
						if opt in self.opts[:4]:
							if not isNumber(data):
								continue
						elif opt in self.opts[4:-2]:
							if data not in ("True", "False"):
								continue
						elif opt in self.opts[-2:]:
							data = data.replace(chr(95), chr(32))
						ConfigDesc.setdefault(title, {})[opt] = data
			if ConfigDesc:
				for (title, opts) in ConfigDesc.items():
					for (opt, data) in opts.items():
						GenCon.set(title, opt, data)
						if opt in self.opts:
							if opt not in self.opts[-2:]:
								data = eval(data)
								if opt == self.opts[0]:
									data *= 1024
									data = (32768 if (data and data <= 32768) else data)
							set_global(self.optsGlobEq[self.opts.index(opt)], data)
				cat_file(GenConFile, self.get_config(GenCon))
				ls = []
				for opts in ConfigDesc.values():
					ls.extend(opts.keys())
				answer = self.AnsBase[0] % ", ".join(opt.upper() for opt in ls)
			else:
				answer = self.AnsBase[1]
		else:
			Message(source[0], self.AnsBase[2] + self.get_config(GenCon), disp)
			if stype == sBase[1]:
				answer = "Sent in private."
		if answer:
			Answer(answer, stype, source, disp)

	def command_cls_config(self, stype, source, body, disp):
		answer = None
		if body:
			args = body.split()
			if len(args) >= 2:
				subcmd = args.pop(0).lower()
				if subcmd in ("del", "delete"):
					Name = args.pop(0).lower()
					if Name in InstancesDesc:
						if Name not in Clients or len(Clients) >= 2:
							if Name == GenDisp:
								remaining = [d for d in Clients if d != GenDisp]
								Gen = choice(remaining)
								delivery(self.AnsBase[6] % Gen)
								set_global("GenDisp", Gen)
							for conf in list(Chats.values()):
								if conf.disp == Name:
									if online(Name):
										Message(conf.name, self.AnsBase[4], Name)
										sleep(0.2)
									conf.leave(self.AnsBase[5])
									conf.disp = IdleClient()
									conf.save()
									sleep(0.6)
									conf.join()
							if online(Name):
								try:
									client = Clients[Name]
									schedule_coro(client.disconnect(), Name)
								except Exception:
									pass
							Guard.pop(Name, None)
							del InstancesDesc[Name]
							Clients.pop(Name, None)

							# Hapus section terkait dari clients.ini (persist)
							for sec in list(ConDisp.sections()):
								try:
									user = ConDisp.get(sec, "user", fallback="").lower()
									host = ConDisp.get(sec, "host", fallback="").lower()
									if "%s@%s" % (user, host) == Name:
										ConDisp.remove_section(sec)
								except Exception:
									pass
							cat_file(ConDispFile, self.get_config(ConDisp))

							answer = "Done. (removed from clients.ini)"
						else:
							answer = self.AnsBase[7]
					else:
						answer = self.AnsBase[11] % Name

				elif subcmd in ("add",):
					if len(args) >= 3:
						host = args.pop(0).lower()
						user = args.pop(0).lower()
						code = args.pop(0)
						port = args.pop(0) if args and args[0].isdigit() else "5222"
						serv = args.pop(0).lower() if args else host
						jid  = "%s@%s" % (user, host)
						if jid not in Clients and jid not in InstancesDesc:
							if connect_client(jid, (serv, int(port), host, user, code))[0]:
								# Persist ke clients.ini — gunakan jid sebagai nama section
								sec = jid.upper()
								if not ConDisp.has_section(sec):
									ConDisp.add_section(sec)
								ConDisp.set(sec, "serv", serv)
								ConDisp.set(sec, "port", port)
								ConDisp.set(sec, "user", user)
								ConDisp.set(sec, "host", host)
								ConDisp.set(sec, "pass", code)
								cat_file(ConDispFile, self.get_config(ConDisp))
								InstancesDesc[jid] = (serv, int(port), host, user, code)
								answer = "Done. (saved to clients.ini)"
							else:
								answer = self.AnsBase[9]
						else:
							answer = self.AnsBase[10]
					else:
						answer = "Not enough arguments."

				elif subcmd in ("password", "pass"):
					if args:
						Name = args.pop(0).lower()
						if Name in InstancesDesc:
							answer = "Password change via command not supported in slixmpp mode."
						else:
							answer = self.AnsBase[11] % Name
					else:
						answer = "No arguments."
				else:
					answer = "Unknown subcommand."
			else:
				answer = "Not enough arguments."
		elif not ConDisp.sections():
			answer = self.AnsBase[3]
		else:
			Message(source[0], self.AnsBase[2] + self.get_config(ConDisp), disp)
			if stype == sBase[1]:
				answer = "Sent in private."
		if answer:
			Answer(answer, stype, source, disp)

	commands = (
		(command_config,     "config", 8,),
		(command_cls_config, "client", 8,)
	)