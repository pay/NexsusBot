# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "muc" # /code.py v.x9
#  Original © (2009-2012) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	sep = chr(47)  # /

	def _bot_role(self, conf):
		"""Return (affiliation, role) tuple of bot in room, or ('none','none')."""
		user = Chats[conf].get_user(Chats[conf].nick) if conf in Chats else None
		return getattr(user, "role", ("none", "none"))

	def _require_conf(self, source):
		return source[1] in Chats

	def _resolve_jid(self, conf, nick):
		"""Return JID from nick or dotted nick string, else None."""
		if Chats[conf].isHere(nick):
			return get_source(conf, nick)
		if "." in nick:
			return nick
		return None

	def _affiliation_cmd(self, stype, source, body, disp, method, min_access=6):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				if Chats[conf].isModer:
					bot_aff = self._bot_role(conf)[0]
					if enough_access(conf, source[2], min_access) or bot_aff != aRoles[5]:
						parts = body.split(self.sep, 1)
						nick  = parts.pop(0).strip()
						jid   = self._resolve_jid(conf, nick)
						if jid:
							reason = ("%s: %s" % (source[2], parts[0].strip())
							         if parts else "%s/%s" % (get_nick(conf), source[2]))
							getattr(Chats[conf], method)(jid, reason)
						else:
							answer = AnsBase[7]
					else:
						answer = self.AnsBase[0]
				else:
					answer = self.AnsBase[1]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def _role_cmd(self, stype, source, body, disp, method, min_access=6):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				bot_role = self._bot_role(conf)
				if Chats[conf].isModer or bot_role[1] == aRoles[9]:
					if enough_access(conf, source[2], min_access) or bot_role[0] != aRoles[5]:
						parts = body.split(self.sep, 1)
						nick  = parts.pop(0).strip()
						jid   = get_source(conf, nick) if Chats[conf].isHere(nick) else None
						if nick and jid:
							if not enough_access(jid, None, 7) and jid != get_disp(disp):
								reason = ("%s: %s" % (source[2], parts[0].strip())
								         if parts else "%s/%s" % (get_nick(conf), source[2]))
								getattr(Chats[conf], method)(nick, reason)
							else:
								answer = AnsBase[7]
						else:
							answer = AnsBase[7]
					else:
						answer = self.AnsBase[0]
				else:
					answer = self.AnsBase[1]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def command_subject(self, stype, source, body, disp):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				Chat     = Chats[conf]
				bot_role = self._bot_role(conf)
				if Chat.isModer or bot_role[1] == aRoles[9]:
					Chat.subject(body)
				else:
					answer = self.AnsBase[1]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def command_ban(self, stype, source, body, disp):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				if Chats[conf].isModer:
					bot_aff = self._bot_role(conf)[0]
					if enough_access(conf, source[2], 6) or bot_aff != aRoles[5]:
						parts = body.split(self.sep, 1)
						nick  = parts.pop(0).strip()
						jid   = self._resolve_jid(conf, nick)
						if jid and not enough_access(jid, None, 7) and jid != get_disp(disp):
							reason = ("%s: %s" % (source[2], parts[0].strip())
							         if parts else "%s/%s" % (get_nick(conf), source[2]))
							Chats[conf].outcast(jid, reason)
						else:
							answer = AnsBase[7]
					else:
						answer = self.AnsBase[0]
				else:
					answer = self.AnsBase[1]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def command_none(self, stype, source, body, disp):
		self._affiliation_cmd(stype, source, body, disp, "none")

	def command_member(self, stype, source, body, disp):
		self._affiliation_cmd(stype, source, body, disp, "member")

	def command_admin(self, stype, source, body, disp):
		conf = source[1]
		if conf in Chats:
			if self._bot_role(conf)[0] == aRoles[5]:
				self._affiliation_cmd(stype, source, body, disp, "admin", min_access=6)
			else:
				Answer(self.AnsBase[1], stype, source, disp)
		else:
			Answer(AnsBase[0], stype, source, disp)

	def command_owner(self, stype, source, body, disp):
		conf = source[1]
		if conf in Chats:
			if self._bot_role(conf)[0] == aRoles[5]:
				self._affiliation_cmd(stype, source, body, disp, "owner", min_access=6)
			else:
				Answer(self.AnsBase[1], stype, source, disp)
		else:
			Answer(AnsBase[0], stype, source, disp)

	def command_kick(self, stype, source, body, disp):
		self._role_cmd(stype, source, body, disp, "kick", min_access=6)

	def command_visitor(self, stype, source, body, disp):
		self._role_cmd(stype, source, body, disp, "visitor", min_access=6)

	def command_participant(self, stype, source, body, disp):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				bot_role = self._bot_role(conf)
				if Chats[conf].isModer or bot_role[1] == aRoles[9]:
					if enough_access(conf, source[2], 6) or bot_role[0] != aRoles[5]:
						parts = body.split(self.sep, 1)
						nick  = parts.pop(0).strip()
						if Chats[conf].isHere(nick):
							reason = ("%s: %s" % (source[2], parts[0].strip())
							         if parts else "%s/%s" % (get_nick(conf), source[2]))
							Chats[conf].participant(nick, reason)
						else:
							answer = AnsBase[7]
					else:
						answer = self.AnsBase[0]
				else:
					answer = self.AnsBase[1]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def command_moder(self, stype, source, body, disp):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				if Chats[conf].isModer:
					parts = body.split(self.sep, 1)
					nick  = parts.pop(0).strip()
					if Chats[conf].isHere(nick):
						reason = ("%s: %s" % (source[2], parts[0].strip())
						         if parts else "%s/%s" % (get_nick(conf), source[2]))
						Chats[conf].moder(nick, reason)
					else:
						answer = AnsBase[7]
				else:
					answer = self.AnsBase[1]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		if answer:
			Answer(answer, stype, source, disp)

	def command_fullban(self, stype, source, body, disp):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				parts = body.split(self.sep, 1)
				nick  = parts.pop(0).strip()
				jid   = self._resolve_jid(conf, nick)
				if jid and not enough_access(jid, None, 7) and jid != get_disp(disp):
					reason = ("%s: %s" % (source[2], parts[0].strip())
					         if parts else "%s/%s" % (get_nick(conf), source[2]))
					for chat in Chats.values():
						chat.outcast(jid, reason)
					answer = AnsBase[4]
				else:
					answer = AnsBase[7]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		Answer(answer, stype, source, disp)

	def command_fullunban(self, stype, source, body, disp):
		answer = None
		conf   = source[1]
		if conf in Chats:
			if body:
				parts = body.split(self.sep, 1)
				nick  = parts.pop(0).strip()
				jid   = self._resolve_jid(conf, nick)
				if jid:
					for chat in Chats.values():
						chat.none(jid)
					answer = AnsBase[4]
				else:
					answer = AnsBase[7]
			else:
				answer = AnsBase[1]
		else:
			answer = AnsBase[0]
		Answer(answer, stype, source, disp)

	commands = (
		(command_subject,     "subject",     3,),
		(command_ban,         "ban",         5,),
		(command_none,        "none",        5,),
		(command_member,      "member",      5,),
		(command_admin,       "admin",       6,),
		(command_owner,       "owner",       6,),
		(command_kick,        "kick",        3,),
		(command_visitor,     "visitor",     3,),
		(command_participant, "participant", 3,),
		(command_moder,       "moder",       5,),
		(command_fullban,     "fullban",     7,),
		(command_fullunban,   "fullunban",   7,),
	)
