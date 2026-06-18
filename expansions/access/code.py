# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "access" # /code.py v.x3
#  Original © (2011) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	AnsBase = (
		"Your access: %s",                          # 0
		"Access of %s: %s",                         # 1
		"%s not found.",                            # 2
		"Global access list is empty.",             # 3
		"Local access list is empty.",              # 4
		"Access list:\n",                           # 5
		"%s is not in access list.",                # 6
		"Access level must be between -1 and 8.",   # 7
		"Access level must be between 0 and 6.",    # 8
		"This user is in global list, use gaccess.", # 9
		"Can't find user %s.",                      # 10
	)

	AccessFile     = dynamic % "access.db"
	ChatAccessFile = "access.db"

	accessDesc = (
		"Visitor", "Participant", "Member", "Moder",
		"Member/Moder", "Admin", "Owner", "Chief", "God"
	)

	def get_acc(self, access):
		if access > 8:
			return "%d (Gandalf)" % access
		elif access < 0:
			return "%d (f7u12)" % access
		return "%d (%s)" % (access, self.accessDesc[access])

	def command_get_access(self, stype, source, body, disp):
		# Fix: strip() body agar spasi trailing tidak menyebabkan not found
		body = body.strip() if body else ""
		if not body:
			answer = self.AnsBase[0] % self.get_acc(get_access(source[1], source[2]))
		elif source[1] in Chats:
			if Chats[source[1]].isHere(body):
				answer = self.AnsBase[1] % (body, self.get_acc(get_access(source[1], body)))
			elif body in Galist:
				answer = self.AnsBase[1] % (body, self.get_acc(Galist[body]))
			elif body in Chats[source[1]].alist:
				answer = self.AnsBase[1] % (body, self.get_acc(Chats[source[1]].alist[body]))
			else:
				answer = self.AnsBase[2] % body
		elif body in Galist:
			answer = self.AnsBase[1] % (body, self.get_acc(Galist[body]))
		else:
			answer = self.AnsBase[2] % body
		Answer(answer, stype, source, disp)

	def command_get_galist(self, stype, source, body, disp):
		answer = None
		if Galist:
			ls = sorted([(acc, user) for user, acc in Galist.items()], reverse=True)
			if stype == sBase[1]:
				answer = "Sending in private..."
			Message(source[0],
			        self.AnsBase[5] + enumerated_list(
			            "%s - %d" % (user, acc) for acc, user in ls), disp)
		else:
			answer = self.AnsBase[3]
		if answer:
			Answer(answer, stype, source, disp)

	def command_get_lalist(self, stype, source, body, disp):
		answer = None
		if source[1] in Chats:
			if Chats[source[1]].alist:
				ls = sorted([(acc, user) for user, acc in Chats[source[1]].alist.items()], reverse=True)
				if stype == sBase[1]:
					answer = "Sending in private..."
				Message(source[0],
				        self.AnsBase[5] + enumerated_list(
				            "%s - %d" % (user, acc) for acc, user in ls), disp)
			else:
				answer = self.AnsBase[4]
		else:
			answer = self.AnsBase[2] % source[1]
		if answer:
			Answer(answer, stype, source, disp)

	def command_set_access(self, stype, source, body, disp):

		def set_access(instance, access=None):
			if access is not None:
				Galist[instance] = access
			else:
				del Galist[instance]
			cat_file(self.AccessFile, str(Galist))
			for conf in Chats.keys():
				for sUser in Chats[conf].get_users():
					if sUser.source == instance:
						if access is not None:
							sUser.access = access
						else:
							local_acc = Chats[conf].alist.get(instance)
							if local_acc is not None:
								sUser.access = local_acc
							else:
								sUser.calc_acc()

		if not body:
			return Answer("No arguments.", stype, source, disp)
		parts = body.split(None, 1)
		if len(parts) != 2:
			return Answer("Invalid arguments.", stype, source, disp)
		access_str, Nick = parts
		Nick     = Nick.strip()
		instance = None
		if source[1] in Chats and Chats[source[1]].isHere(Nick):
			instance = get_source(source[1], Nick)
		if not instance:
			candidate = Nick.split()[0].lower()
			instance  = candidate if isSource(candidate) else None
		if not instance:
			return Answer(self.AnsBase[10] % Nick, stype, source, disp)
		if access_str == "!":
			if instance in Galist:
				set_access(instance)
				answer = "Done."
			else:
				answer = self.AnsBase[6] % Nick
		elif isNumber(access_str):
			access = int(access_str)
			if -1 <= access <= 8:
				set_access(instance, access)
				answer = "Done."
			else:
				answer = self.AnsBase[7]
		else:
			answer = "Invalid arguments."
		Answer(answer, stype, source, disp)

	def command_set_local_access(self, stype, source, body, disp):

		def set_access(conf, instance, access=None):
			if access is not None:
				Chats[conf].alist[instance] = access
			else:
				del Chats[conf].alist[instance]
			cat_file(chat_file(conf, self.ChatAccessFile), str(Chats[conf].alist))
			for sUser in Chats[conf].get_users():
				if sUser.source == instance:
					if access is not None:
						sUser.access = access
					else:
						global_acc = Galist.get(instance)
						if global_acc is not None:
							sUser.access = global_acc
						else:
							sUser.calc_acc()

		if source[1] not in Chats:
			return Answer(self.AnsBase[2] % source[1], stype, source, disp)
		if not body:
			return Answer("No arguments.", stype, source, disp)
		parts = body.split(None, 1)
		if len(parts) != 2:
			return Answer("Invalid arguments.", stype, source, disp)
		access_str, Nick = parts
		Nick     = Nick.strip()
		instance = None
		if Chats[source[1]].isHere(Nick):
			instance = get_source(source[1], Nick)
		if not instance:
			candidate = Nick.split()[0].lower()
			instance  = candidate if isSource(candidate) else None
		if not instance:
			return Answer(self.AnsBase[10] % Nick, stype, source, disp)
		if access_str == "!":
			if instance in Chats[source[1]].alist:
				set_access(source[1], instance)
				answer = "Done."
			else:
				answer = self.AnsBase[6] % Nick
		elif instance in Galist:
			answer = self.AnsBase[9]
		elif isNumber(access_str):
			access = int(access_str)
			if 0 <= access <= 6:
				set_access(source[1], instance, access)
				answer = "Done."
			else:
				answer = self.AnsBase[8]
		else:
			answer = "Invalid arguments."
		Answer(answer, stype, source, disp)

	def load_acclist(self):
		if initialize_file(self.AccessFile):
			try:
				Galist.update(eval(get_file(self.AccessFile)))
			except Exception:
				pass

	def load_local_acclist(self, conf):
		filename = chat_file(conf, self.ChatAccessFile)
		if initialize_file(filename):
			try:
				Chats[conf].alist.update(eval(get_file(filename)))
			except Exception:
				pass

	commands = (
		(command_get_access,       "access",   1,),
		(command_get_galist,       "acclist",  7,),
		(command_get_lalist,       "acclist2", 4,),
		(command_set_access,       "gaccess",  8,),
		(command_set_local_access, "laccess",  6,),
	)

	handlers = (
		(load_acclist,       "00si"),
		(load_local_acclist, "01si"),
	)