# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus port
# exp_name = "cmd_control" # /code.py v.x2
#  Id: 32~2c
#  Code © (2012) by WitcherGeralt [alkorgun@gmail.com]

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	TabooFile = "taboo.db"

	# Canned reply strings (replaces old shared AnsBase list)
	Ans = (
		"Command '%s' removed from taboo list.",   # 0 — un-taboo'd
		"Command '%s' added to taboo list.",        # 1 — taboo'd
		"This command cannot be taboo'd.",          # 2 — in sCmds (prefix-less)
		"Taboo list is empty.",                     # 3 — no oCmds
	)

	def command_taboo(self, stype, source, body, disp):
		if source[1] in Chats:
			oCmds = Chats[source[1]].oCmds
			if body:
				if enough_access(source[1], source[2], 6):
					ls = body.split()
					command = ls.pop(0).lower()
					if command in Cmds:
						if enough_access(source[1], source[2], Cmds[command].access):
							if command not in sCmds:
								if command in oCmds:
									oCmds.remove(command)
									answer = self.Ans[0] % command
								else:
									oCmds.append(command)
									answer = self.Ans[1] % command
								cat_file(chat_file(source[1], self.TabooFile), str(oCmds))
							else:
								answer = self.Ans[2]
						else:
							answer = "Access denied."
					elif command in oCmds:
						oCmds.remove(command)
						answer = self.Ans[0] % command
						cat_file(chat_file(source[1], self.TabooFile), str(oCmds))
					else:
						answer = "Unknown command: %s" % command
				else:
					answer = "Access denied."
			elif oCmds:
				answer = ", ".join(oCmds)
			else:
				answer = self.Ans[3]
		else:
			answer = "This command is only available in group chats."
		Answer(answer, stype, source, disp)

	def init_taboo(self, conf):
		filename = chat_file(conf, self.TabooFile)
		if initialize_file(filename, "[]"):
			Chats[conf].oCmds = eval(get_file(filename))

	commands = ((command_taboo, "taboo", 1, False),)

	handlers = ((init_taboo, "01si"),)