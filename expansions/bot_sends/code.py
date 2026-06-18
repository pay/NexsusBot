# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2
# exp_name = "bot_sends" # /code.py v.x10 — ported to Python 3
#  Code © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]

class expansion_temp(expansion):

	AnsBase = (
		"Clearing...",                        # 0
		"All systems operational.",           # 1
		"%s, errors detected: %d",            # 2
		"Errors: %d",                         # 3
		"",                                   # 4 (unused)
		"%s: %s",                             # 5
		"Already here.",                      # 6
		"Can't find user.",                   # 7
		"Cooldown: %s",                       # 8
		"Nothing to clear.",                  # 9
	)

	def __init__(self, name):
		expansion.__init__(self, name)

	def command_clear(self, stype, source, body, disp):
		answer = None
		conf = source[1]
		if conf in Chats:
			if ChatsAttrs[conf]["dirt"]:
				ChatsAttrs[conf]["dirt"] = None
				if stype == sBase[1]:
					s1_backup = Chats[conf].state
					s2_backup = Chats[conf].status
					Chats[conf].change_status(sList[2], self.AnsBase[0])
				for Numb in range(24):
					if conf not in Chats:
						raise SelfExc("exit")
					Message(conf, " ", disp)
					Info["omsg"].plus()
					if Numb != 23:
						sleep(1.4)
				if stype == sBase[1]:
					Chats[conf].change_status(s1_backup, s2_backup)
				ChatsAttrs[conf]["dirt"] = True
			else:
				answer = self.AnsBase[9]
		else:
			answer = "Not in a chat."
		if answer:
			Answer(answer, stype, source, disp)

	def command_test(self, stype, source, body, disp):
		errors = len(VarCache["errors"])
		if not errors:
			answer = self.AnsBase[1]
		elif errors < (len(Clients.keys()) * 3):
			answer = self.AnsBase[2] % (get_nick(source[1]), errors)
		else:
			answer = self.AnsBase[3] % (errors)
		Answer(answer, stype, source, disp)

	def command_sendall(self, stype, source, body, disp):
		if body:
			for conf in Chats.keys():
				Message(conf, self.AnsBase[5] % (source[2], body))
			answer = "Done."
		else:
			answer = "No arguments."
		Answer(answer, stype, source, disp)

	def command_more(self, stype, source, body, disp):
		Chat = Chats.get(source[1])
		if not Chat:
			return Answer("Not in a chat.", stype, source, disp)
		if Chat.more:
			body = "[&&] %s" % Chat.more
			Chat.more = ""
			Message(Chat.name, body, disp)

	compile_chat = compile__(r"^[^\s'\"@<>&]+?@(?:conference|muc|conf|chat|group)\.[\w-]+?\.[\.\w-]+?$")

	def command_send(self, stype, source, body, disp):
		if body:
			body = body.split(None, 1)
			if len(body) == 2:
				sTo, body = body
				if isSource(sTo):
					conf = sTo.split(chr(47))[0].lower()
					if conf in Chats or not self.compile_chat.match(conf):
						Message(sTo, self.AnsBase[5] % (source[2], body))
						answer = "Done."
					else:
						answer = "Not joined to that room."
				else:
					answer = self.AnsBase[4]
			else:
				answer = "Invalid arguments."
		else:
			answer = "No arguments."
		Answer(answer, stype, source, disp)

	def command_toadmin(self, stype, source, body, disp):
		if body:
			if PrivLimit >= len(body):
				instance = get_source(source[1], source[2])
				delivery(self.AnsBase[5] % (
					(source[2] if not instance else "%s (%s)" % (source[2], instance)), body))
				answer = "Done."
			else:
				answer = "Message too long."
		else:
			answer = "No arguments."
		Answer(answer, stype, source, disp)

	def command_echo(self, stype, source, body, disp):
		if not body:
			return Answer("No arguments.", stype, source, disp)
		if ConfLimit >= len(body):
			Message(source[1], body, disp)
		else:
			Message(source[1], body[:ConfLimit], disp)

	def command_invite(self, stype, source, body, disp):
		import time as _time
		if source[1] in Chats:
			if body:
				Time  = _time.time()
				admin = enough_access(source[1], source[2], 7)
				timer = (720 if admin else (Time - ChatsAttrs[source[1]]["intr"]))
				if timer >= 720:
					source_, arg0 = None, body.split()[0]
					if Chats[source[1]].isHere(body):
						if Chats[source[1]].isHereTS(body):
							return Answer(self.AnsBase[6] % body, stype, source, disp)
						source_ = get_source(source[1], body)
					elif isSource(arg0):
						source_ = arg0.lower()
					if source_:
						if not admin:
							ChatsAttrs[source[1]]["intr"] = Time
						# Send MUC invite via slixmpp
						client = Clients.get(get_disp(disp))
						if client:
							client._schedule(client._send_muc_invite(source[1], source_, source[2]))
						answer = "Done."
					else:
						answer = self.AnsBase[7]
				else:
					answer = self.AnsBase[8] % Time2Text(720 - timer)
			else:
				answer = "No arguments."
		else:
			answer = "Not in a chat."
		Answer(answer, stype, source, disp)

	def init_bot_sender(self, chat):
		desc = ChatsAttrs.setdefault(chat, {})
		desc["intr"] = 0
		desc["dirt"] = True

	commands = (
		(command_clear,   "clear",   3,),
		(command_test,    "test",    1, False),
		(command_sendall, "sendall", 8,),
		(command_more,    "more",    1,),
		(command_send,    "send",    8,),
		(command_toadmin, "toadmin", 1,),
		(command_echo,    "echo",    6,),
		(command_invite,  "invite",  4,)
	)

	handlers = ((init_bot_sender, "01si"),)