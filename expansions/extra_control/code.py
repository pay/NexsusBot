# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "extra_control" # /code.py v.x12
#  Original © (2009-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	sep     = chr(38) * 2   # &&
	pointer = chr(62) * 2   # >>

	def command_turbo(self, stype, source, body, disp):
		answer = None
		if body:
			if self.sep in body:
				ls = [b.strip() for b in body.split(self.sep)]
				if all(ls):
					lslen = len(ls) - 1
					if lslen < 4 or enough_access(source[1], source[2], 7):
						for numb, part in enumerate(ls):
							parts = part.split(None, 1)
							cmd   = parts.pop(0).lower()
							if cmd in Cmds:
								Cmds[cmd].execute(stype, source, parts[0] if parts else "", disp)
								if numb not in (0, lslen):
									sleep(2)
							else:
								answer = AnsBase[6]
					else:
						answer = AnsBase[10]
				else:
					answer = AnsBase[2]
			else:
				answer = AnsBase[2]
		else:
			answer = AnsBase[1]
		if answer:
			Answer(answer, stype, source, disp)

	def command_remote(self, stype, source, body, disp):
		answer = None
		confs  = sorted(Chats.keys())
		if body:
			parts = body.split(None, 3)
			if len(parts) >= 3:
				arg0 = parts.pop(0).lower()
				if arg0 in confs:
					conf = arg0
				elif isNumber(arg0):
					idx = int(arg0) - 1
					conf = confs[idx] if 0 <= idx < len(confs) else None
				else:
					conf = None
				if conf:
					st = parts.pop(0).lower()
					if st in ("chat", "чат"):
						stype_ = sBase[1]
					elif st in ("private", "приват"):
						stype_ = sBase[0]
					else:
						stype_ = None
					if stype_:
						cmd  = parts.pop(0).lower()
						body = parts[0] if parts else ""
						if len(body) <= 2048:
							if cmd in Cmds:
								c = Cmds[cmd]
								if c.isAvailable and c.handler:
									disp_ = Chats[conf].disp if stype_ == sBase[1] else get_disp(disp)
									Info["cmd"].plus()
									sThread("command", c.handler,
									        (c.exp, stype_, (source[0], conf, source[2]), body, disp_), c.name)
									c.numb.plus()
									src = get_source(source[1], source[2])
									if src:
										c.desc.add(src)
								else:
									answer = AnsBase[19] % c.name
							else:
								answer = AnsBase[6]
						else:
							answer = AnsBase[5]
					else:
						answer = AnsBase[9]
				else:
					answer = AnsBase[8]
			else:
				answer = AnsBase[2]
		else:
			answer = enumerated_list(confs)
		if answer:
			Answer(answer, stype, source, disp)

	def command_private(self, stype, source, body, disp):
		answer = None
		if source[1] in Chats:
			if body:
				parts = body.split(None, 1)
				cmd   = parts.pop(0).lower()
				if cmd in Cmds:
					Cmds[cmd].execute(sBase[0], source, parts[0] if parts else "", disp)
				else:
					answer = AnsBase[6]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def command_redirect(self, stype, source, body, disp):
		answer = None
		if source[1] in Chats:
			if body:
				if body.count(self.pointer) >= 1:
					parts = body.split(None, 1)
					cmd   = parts.pop(0).lower()
					if cmd in Cmds:
						c = Cmds[cmd]
						if enough_access(source[1], source[2], c.access):
							if c.isAvailable and c.handler:
								if parts:
									split = parts[0].rsplit(self.pointer, 1)
									if len(split) == 2:
										body_, nick = split[0].strip(), split[1].strip()
									else:
										body_, nick = "", split[0].strip()
								else:
									body_, nick = "", ""
								if Chats[source[1]].isHereTS(nick):
									Info["cmd"].plus()
									sThread("command", c.handler,
									        (c.exp, sBase[0],
									         ("%s/%s" % (source[1], nick), source[1], nick),
									         body_, disp), c.name)
									c.numb.plus()
									src = get_source(source[1], source[2])
									if src:
										c.desc.add(src)
									answer = AnsBase[4]
								else:
									answer = AnsBase[7]
							else:
								answer = AnsBase[19] % c.name
						else:
							answer = AnsBase[10]
					else:
						answer = AnsBase[6]
				else:
					answer = AnsBase[2]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		Answer(answer, stype, source, disp)

	commands = (
		(command_turbo,    "turbo",    1,),
		(command_remote,   "remote",   8,),
		(command_private,  "private",  1,),
		(command_redirect, "redirect", 5,),
	)
