# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "help" # /code.py v.x7
#  Id: 03~4c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AnsBase = (
		"Command '%s' is from expansion: %s",   # 0
		"Command '%s' requires access: %d",     # 1
		"%s\n%s",                                # 2  help header
		"Usage:",                                # 3
		"No help file found.",                   # 4
		"Commands list — use 'commands'.",       # 5
		"Commands (prefix '%s'):",               # 6
		"'%s'",                                  # 7  prefix display
		"\n[8/God+] (%d): %s",                  # 8
		"\n[7/Chief] (%d): %s",                 # 9
		"\n[6] (%d): %s",                        # 10
		"\n[5] (%d): %s",                        # 11
		"\n[4] (%d): %s",                        # 12
		"\n[3] (%d): %s",                        # 13
		"\n[2] (%d): %s",                        # 14
		"\n[1/All] (%d): %s",                    # 15
		"\nYour access: %s",                     # 16
		"Help file format error.",               # 17
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
			return Answer("Unknown command.", stype, source, disp)
		if parts:
			lang = parts.pop(0).lower()
			if len(lang) == 2 and lang.isalpha():
				helpf = os.path.join(ExpsDir, Cmds[command].exp.name,
				                     "%s.%s" % (Cmds[command].default, lang))
			else:
				helpf = None
		else:
			helpf = Cmds[command].help
		if helpf and os.path.isfile(helpf):
			text = get_file(helpf)
			if self.mark in text:
				text  = text.format(command=command)
				lines = text.splitlines()
				if len(lines) >= 2:
					ls = [self.AnsBase[2] % (lines.pop(0), lines.pop(0))]
					if lines:
						ls.append(self.AnsBase[3])
						for line in lines:
							line = line.strip()
							if line.startswith("*/"):
								# Fix: unichr(187) → chr(187)
								Char = chr(187) * 3
								line = line[2:].lstrip()
							else:
								Char = chr(9) + chr(42)
							ls.append("%s %s" % (Char, line))
					answer = "\n".join(ls)
				else:
					answer = self.AnsBase[17]
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
		# Count cumulative accessible commands per access level
		lcmds  = {x: 0 for x in range(1, 9)}
		for cmd in Cmds.keys():
			access = Cmds[cmd].access
			cmds.setdefault(access, []).append(cmd)
			for x in lcmds:
				if x >= access:
					lcmds[x] += 1
		for ls in cmds.values():                 # Fix: itervalues → values
			ls.sort()
		for level, fmt_idx in ((8, 8), (7, 9), (6, 10), (5, 11),
		                       (4, 12), (3, 13), (2, 14), (1, 15)):
			if level in cmds:
				answer += self.AnsBase[fmt_idx] % (lcmds[level], ", ".join(cmds[level]))
		access = get_access(source[1], source[2])
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
			Answer("Sent to PM.", stype, source, disp)
		Message(source[0], answer, disp)

	commands = (
		(command_location, "location", 1,),
		(command_comacc,   "comacc",   1,),
		(command_help,     "help",     1, False),
		(command_commands, "commands", 1, False),
	)