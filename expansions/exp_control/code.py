# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "exp_control" # /code.py v.x9
#  Id: 09~9c
#  Original © (2011-2012) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AnsBase = (
		"Expansion info:",                                        # 0
		"exists",                                                 # 1
		"missing",                                                # 2
		"loaded",                                                 # 3
		"Done.",                                                  # 4
		" handlers: %s",                                          # 5
		"not loaded",                                             # 6
		"Not found.",                                             # 7
		"Expansions:",                                            # 8
		"\nUnloaded (%d):\n%s",                                   # 9
		"Expansion '%s' loaded.",                                 # 10
		"Failed to load '%s': %s",                               # 11
		"",                                                       # 12
		" Previous version restored.",                            # 13
		"Available handlers: %s",                                 # 14
		"No handlers in '%s'.",                                   # 15
		"Command '%s' is already enabled.",                       # 16
		"Command '%s' is already disabled.",                      # 17
		"All commands are enabled.",                              # 18
	)

	def command_expinfo(self, stype, source, body, disp):
		get_state = lambda filename: (self.AnsBase[1] if filename and os.path.isfile(filename) else self.AnsBase[2])
		if body:
			exp_name = body.lower()
			if exp_name in expansions:                            # Fix: has_key → in
				answer = self.AnsBase[0]
				code_file = get_state(expansions[exp_name].file)
				answer += "\n%s - %s - %s" % (exp_name, self.AnsBase[3], code_file)
				if expansions[exp_name].cmds:
					answer += "\n commands: %s" % ", ".join(expansions[exp_name].cmds)
				if expansions[exp_name].desc:
					answer += self.AnsBase[5] % "; ".join(
						"%s: (%s)" % (eh, ", ".join(i.__name__ for i in ls))
						for eh, ls in sorted(expansions[exp_name].desc.items()))
			else:
				exp = expansion(exp_name)
				if os.path.exists(exp.path):
					answer = self.AnsBase[0]
					code_file = get_state(exp.file)
					answer += "\n%s - %s - %s" % (exp_name, self.AnsBase[6], code_file)
				else:
					answer = self.AnsBase[7]
		else:
			lines  = [self.AnsBase[8]]
			number = 0
			for exp_name in sorted(expansions.keys()):
				number += 1
				code_file = get_state(expansions[exp_name].file)
				lines.append("%d) %s - %s" % (number, exp_name, code_file))
			elexps = []
			for exp_name in sorted(os.listdir(ExpsDir)):
				if exp_name.startswith(".") or exp_name in expansions:  # Fix: has_key → in
					continue
				if os.path.isdir(os.path.join(ExpsDir, exp_name)):
					number += 1
					exp = expansion(exp_name)
					code_file = get_state(exp.file)
					elexps.append("%d) %s - %s" % (number, exp_name, code_file))
			if elexps:
				lines.append(self.AnsBase[9] % (len(elexps), "\n".join(elexps)))
			answer = "\n".join(lines)
		Answer(answer, stype, source, disp)

	ReloadSemaphore = threading.Semaphore()   # Fix: ithr.Semaphore → threading.Semaphore

	def command_expload(self, stype, source, body, disp):
		if body:
			exp_name = body.strip("\\/").lower()
			exp = expansion(exp_name)
			if exp.isExp:
				backup = expansions.get(exp_name)
				with self.ReloadSemaphore:
					exp, exc = exp.load()
					if exp:
						try:
							exp.initialize_exp()
						except Exception:
							exc = exc_info()
							exp.dels(True)
							answer = self.AnsBase[11] % (exp_name, "\n\t* %s: %s" % exc)
							if backup:
								backup.initialize_exp()
								backup.initialize_all()
								answer += self.AnsBase[13]
						else:
							exp.initialize_all()
							answer = self.AnsBase[10] % exp_name
					else:
						answer = self.AnsBase[11] % (exp_name, "\n\t* %s: %s" % exc)
						if backup:
							backup.initialize_exp()
							backup.initialize_all()
							answer += self.AnsBase[13]
			else:
				answer = self.AnsBase[7]
		else:
			answer = self.AnsBase[7]
		Answer(answer, stype, source, disp)

	def command_expunload(self, stype, source, body, disp):
		if body:
			parts    = body.split()
			exp_name = parts.pop(0).lower()
			if exp_name in expansions:                            # Fix: has_key → in
				if parts:
					handler, Name = None, parts.pop(0)
					all_names = []
					for ls in expansions[exp_name].desc.values():
						for instance in ls:
							inst = instance.__name__
							all_names.append(inst)
							if inst == Name:
								handler = instance
					if handler:
						with self.ReloadSemaphore:
							expansions[exp_name].clear_handlers(handler)
						answer = self.AnsBase[4]
					elif all_names:
						answer = self.AnsBase[14] % ", ".join(sorted(all_names))
					else:
						answer = self.AnsBase[15] % exp_name
				else:
					with self.ReloadSemaphore:
						expansions[exp_name].dels(True)
					answer = self.AnsBase[4]
			else:
				answer = self.AnsBase[7]
		else:
			answer = self.AnsBase[7]
		Answer(answer, stype, source, disp)

	def command_tumbler(self, stype, source, body, disp):
		if body:
			parts   = body.split()
			command = parts.pop(0).lower()
			if command in Cmds:                                   # Fix: has_key → in
				cmd = Cmds[command]
				if parts:
					action = parts.pop(0).lower()
					# Fix: "вкл".decode("utf-8") → literal string
					if action in ("on", "1", "вкл"):
						if not cmd.isAvailable:
							if cmd.handler:
								cmd.isAvailable = True
								answer = self.AnsBase[4]
							else:
								answer = "Command '%s' has no handler." % command
						else:
							answer = self.AnsBase[16] % command
					elif action in ("off", "0", "выкл"):
						if cmd.isAvailable:
							if cmd.handler:
								cmd.isAvailable = False
								answer = self.AnsBase[4]
							else:
								answer = "Command '%s' has no handler." % command
						else:
							answer = self.AnsBase[17] % command
					else:
						answer = "Use: on/off"
				else:
					answer = self.AnsBase[16 if cmd.isAvailable else 17] % command
			else:
				answer = "Unknown command."
		else:
			# Fix: iteritems → items
			disabled = [c for c, cmd in Cmds.items() if not cmd.isAvailable]
			answer   = ", ".join(disabled) if disabled else self.AnsBase[18]
		Answer(answer, stype, source, disp)

	commands = (
		(command_expinfo,   "expinfo",   7,),
		(command_expload,   "expload",   8,),
		(command_expunload, "expunload", 8,),
		(command_tumbler,   "tumbler",   8,),
	)