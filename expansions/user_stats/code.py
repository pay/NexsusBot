# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "user_stats" # /code.py v.x7
#  Id: 17~6c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		# Fix: check_sqlite() → tidak ada di Nexus, SQLite sudah built-in Python 3
		expansion.__init__(self, name)

	UstatsFile = "jstat.db"
	UstatsDesc = {}

	# Fix: database() → Database(), cefile() → path langsung
	def db(self, conf):
		sem = self.UstatsDesc.get(conf)
		return Database(chat_file(conf, self.UstatsFile), sem)

	AnsBase = (
		"Joined: %s\nDate: %s\nRole: %s",          # 0
		"\nLast seen: %s\nLeft: %s",               # 1
		"\nNicks: %s",                              # 2
		"No data.",                                 # 3
		"%s has been here for %s.",                 # 4
		"You have been here for %s.",               # 5
		"Not here.",                                # 6
	)

	def command_user_stats(self, stype, source, body, disp):
		if source[1] not in Chats:                  # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		if not body:
			body = get_source(source[1], source[2])
		elif Chats[source[1]].isHere(body):
			body = get_source(source[1], body)
		with self.db(source[1]) as db:
			db("SELECT * FROM stat WHERE jid=?", (body,))
			row = db.fetchone()
		if row:
			answer = self.AnsBase[0] % (row[3], row[2], row[1])
			if row[3] >= 2 and row[4]:
				answer += self.AnsBase[1] % (row[4], row[5])
			answer += self.AnsBase[2] % ", ".join(sorted(row[6].split("-/-")))
		else:
			answer = self.AnsBase[3]
		Answer(answer, stype, source, disp)

	def command_here(self, stype, source, nick, disp):
		if source[1] not in Chats:                  # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		if not nick:
			nick = source[2]
		if Chats[source[1]].isHereTS(nick):
			jtc = Time2Text(time.time() - Chats[source[1]].get_user(nick).date[0])
			if nick != source[2]:
				answer = self.AnsBase[4] % (nick, jtc)
			else:
				answer = self.AnsBase[5] % jtc
		else:
			answer = self.AnsBase[6]
		Answer(answer, stype, source, disp)

	def calc_stat_04eh(self, conf, nick, instance, role, stanza, disp):
		if not instance or nick == get_nick(conf):
			return
		date = strfTime(local=False)
		with self.db(conf) as db:
			db("SELECT * FROM stat WHERE jid=?", (instance,))
			row = db.fetchone()
			if row:
				db("UPDATE stat SET joined=?, joins=? WHERE jid=?",
				   (date, row[3] + 1, instance))
				if nick not in row[6].split("-/-"):
					db("UPDATE stat SET nicks=? WHERE jid=?",
					   ("%s-/-%s" % (row[6], nick), instance))
				arole = "%s/%s" % role
				if row[1] != arole:
					db("UPDATE stat SET arole=? WHERE jid=?", (arole, instance))
			else:
				db("INSERT INTO stat VALUES (?,?,?,?,?,?,?)",
				   (instance, "%s/%s" % role, date, 1, "", "", nick))
			db.commit()

	def calc_stat_05eh(self, conf, nick, sbody, scode, disp):
		if nick == get_nick(conf):
			return
		source_ = get_source(conf, nick)
		if not source_:
			return
		if scode == sCodes[0]:
			sbody = "banned:(%s)" % sbody
		elif scode == sCodes[2]:
			sbody = "kicked:(%s)" % sbody
		date = strfTime(local=False)
		with self.db(conf) as db:
			db("SELECT * FROM stat WHERE jid=?", (source_,))
			if db.fetchone():
				# Fix: unicode() → str() (Python 3)
				db("UPDATE stat SET seen=?, leave=? WHERE jid=?",
				   (date, str(sbody), source_))
				db.commit()

	def calc_stat_06eh(self, conf, old_nick, nick, disp):
		if nick == get_nick(conf):
			return
		source_ = get_source(conf, nick)
		if not source_:
			return
		with self.db(conf) as db:
			db("SELECT * FROM stat WHERE jid=?", (source_,))
			row = db.fetchone()
			if row and nick not in row[6].split("-/-"):
				db("UPDATE stat SET nicks=? WHERE jid=?",
				   ("%s-/-%s" % (row[6], nick), source_))
				db.commit()

	def calc_stat_07eh(self, conf, nick, role, disp):
		if nick == get_nick(conf):
			return
		source_ = get_source(conf, nick)
		if not source_:
			return
		with self.db(conf) as db:
			db("SELECT * FROM stat WHERE jid=?", (source_,))
			row = db.fetchone()
			if row:
				arole = "%s/%s" % role
				if row[1] != arole:
					db("UPDATE stat SET arole=? WHERE jid=?", (arole, source_))
					db.commit()

	def init_stat_base(self, conf):
		filename = chat_file(conf, self.UstatsFile)
		# Buat direktori jika belum ada
		folder = os.path.dirname(filename)
		if folder and not os.path.exists(folder):
			os.makedirs(folder, exist_ok=True)
		if not os.path.isfile(filename):
			with Database(filename) as db:
				db("CREATE TABLE IF NOT EXISTS stat "
				   "(jid TEXT, arole TEXT, joined TEXT, joins INTEGER, "
				   "seen TEXT, leave TEXT, nicks TEXT)")
				db.commit()
		# Fix: ithr.Semaphore() → threading.Semaphore()
		self.UstatsDesc[conf] = threading.Semaphore()

	def edit_stat_desc(self, conf):
		self.UstatsDesc.pop(conf, None)

	commands = (
		(command_user_stats, "userstat", 2,),
		(command_here,       "here",     1,),
	)

	handlers = (
		(init_stat_base,    "01si"),
		(edit_stat_desc,    "04si"),
		(calc_stat_04eh,    "04eh"),
		(calc_stat_05eh,    "05eh"),
		(calc_stat_06eh,    "06eh"),
		(calc_stat_07eh,    "07eh"),
	)