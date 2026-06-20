# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3 / slixmpp)
# exp_name = "roster_control" # /code.py v.x5

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	RosterFile = dynamic % "roster.db"

	def _get_roster(self, name):
		client = Clients.get(name)
		if client and hasattr(client, "client_roster"):
			return client.client_roster
		return None

	def command_roster(self, stype, source, body, disp):
		cls    = sorted(Clients.keys())
		answer = None
		if body:
			body = body.split()
			arg0 = body.pop(0).lower()
			if arg0 in cls:
				Name = arg0
			elif isNumber(arg0):
				idx = int(arg0) - 1
				Name = cls[idx] if 0 <= idx < len(cls) else None
			else:
				Name = None

			if Name:
				if body:
					action = body.pop(0)
					if body:
						jid = body.pop(0).lower()
						if "." in jid:
							roster = self._get_roster(Name)
							if roster is not None:
								if action == "+":
									Clients[Name].send_presence(pto=jid, ptype="subscribe")
									Clients[Name].send_presence(pto=jid, ptype="subscribed")
									nick  = body.pop(0) if body else jid.split("@")[0]
									group = "Admins" if body and body.pop(0).lower() in ("admin", "админ") else "Users"
									try:
										roster[jid]["name"]   = nick
										roster[jid]["groups"] = [group]
									except Exception:
										pass
									answer = AnsBase[4]
								elif action == "-":
									if jid in roster:
										Clients[Name].send_presence(pto=jid, ptype="unsubscribe")
										Clients[Name].send_presence(pto=jid, ptype="unsubscribed")
										try:
											del roster[jid]
										except Exception:
											pass
										answer = AnsBase[4]
									else:
										answer = self.AnsBase[0]
								else:
									answer = AnsBase[2]
							else:
								answer = AnsBase[7]
						else:
							answer = AnsBase[2]
					else:
						answer = AnsBase[2]
				else:
					roster = self._get_roster(Name)
					if roster is not None:
						jids = [j for j in roster.keys() if "@conference." not in j]
						if jids:
							Groups = {None: []}
							for jid in jids:
								try:
									nick = roster[jid]["name"] or None
									grps = roster[jid]["groups"]
									gp   = sorted(grps)[0] if grps else None
								except Exception:
									nick, gp = None, None
								if gp and gp not in Groups:
									Groups[gp] = []
								Groups.setdefault(gp, []).append((jid, nick))
							ls    = ["[Group] [#] [JID] (Nick)"]
							nogrp = Groups.pop(None, [])
							ctr   = [0]
							def _num():
								ctr[0] += 1
								return ctr[0]
							for gp, items in sorted(Groups.items()) + [("No Group", nogrp)]:
								if items:
									ls.append(gp + ":")
									for jid, nick in sorted(items):
										if nick and nick != jid:
											ls.append("\t%d) %s - %s" % (_num(), jid, nick))
										else:
											ls.append("\t%d) %s" % (_num(), jid))
							answer = "\n".join(ls)
						else:
							answer = self.AnsBase[1]
					else:
						answer = self.AnsBase[1]
			else:
				answer = self.AnsBase[2]
		else:
			answer = enumerated_list(cls)

		if answer is not None:
			Answer(answer, stype, source, disp)

	def command_roster_state(self, stype, source, body, disp):
		if body:
			body = body.split()[0].lower()
			if body in ("on", "1", "вкл"):
				if not Roster["on"]:
					Roster["on"] = True
					cat_file(self.RosterFile, str(True))
					answer = AnsBase[4]
				else:
					answer = self.AnsBase[3]
			elif body in ("off", "0", "выкл"):
				if Roster["on"]:
					Roster["on"] = False
					cat_file(self.RosterFile, str(False))
					answer = AnsBase[4]
				else:
					answer = self.AnsBase[4]
			else:
				answer = AnsBase[2]
		else:
			answer = self.AnsBase[3] if Roster["on"] else self.AnsBase[4]
		Answer(answer, stype, source, disp)

	def init_roster_state(self):
		if initialize_file(self.RosterFile, str(True)):
			Roster["on"] = eval(get_file(self.RosterFile))

	commands = (
		(command_roster,       "roster",  7,),
		(command_roster_state, "roster2", 7,),
	)

	handlers = ((init_roster_state, "00si"),)