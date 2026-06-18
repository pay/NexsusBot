# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "talkers" # /code.py v.x6
#  Id: 14~5c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		# Fix: check_sqlite() → tidak ada, SQLite built-in Python 3
		expansion.__init__(self, name)

	TalkersFile = "talkers.db"
	TalkersDesc = {}

	def db(self, conf):
		return Database(chat_file(conf, self.TalkersFile), self.TalkersDesc.get(conf))

	AnsBase = (
		"Top talkers:",                             # 0
		"No data.",                                 # 1
		"Messages: %d\nWords: %d\nWords/msg: %s",  # 2
		"\n(showing partial results)",              # 3
	)

	def command_talkers(self, stype, source, body, disp):
		if source[1] not in Chats:                 # Fix: has_key → in
			return Answer("Not in a room.", stype, source, disp)
		if not body:
			return Answer("Not enough arguments.", stype, source, disp)

		ls  = body.split()
		a1  = ls.pop(0).lower()

		if len(ls) < 1:
			return Answer("Not enough arguments.", stype, source, disp)

		# Fix: all .decode("utf-8") → literals
		if a1 in ("top", "топ"):
			a2 = ls.pop(0).lower()
			limit = 10
			if ls and isNumber(ls[0]):
				limit = min(int(ls.pop(0)), 256)

			if a2 in ("local", "локальный"):
				with self.db(source[1]) as db:
					db("SELECT * FROM talkers ORDER BY msgs DESC")
					rows = db.fetchall()
				rows = rows[:limit]
				if rows:
					lines = [self.AnsBase[0]]
					for i, x in enumerate(rows, 1):
						avg = round(x[3] / x[2], 1) if x[2] else 0
						lines.append("%d. %s\t\t%d\t%d\t%s" % (i, x[1], x[2], x[3], avg))
					answer = "\n".join(lines)
				else:
					answer = self.AnsBase[1]

			elif a2 in ("global", "глобальный"):
				glob = {}
				for conf in Chats.keys():
					with self.db(conf) as db:
						db("SELECT * FROM talkers ORDER BY msgs DESC")
						rows = db.fetchall()
					for x in rows:
						if x[0] in glob:        # Fix: has_key → in
							glob[x[0]][2] += x[2]
							glob[x[0]][3] += x[3]
						else:
							glob[x[0]] = list(x)
				if glob:
					top = sorted(glob.values(), key=lambda x: x[2], reverse=True)[:limit]
					lines = [self.AnsBase[0]]
					for i, x in enumerate(top, 1):
						avg = round(x[3] / x[2], 1) if x[2] else 0
						lines.append("%d. %s\t\t%d\t%d\t%s" % (i, x[1], x[2], x[3], avg))
					answer = "\n".join(lines)
				else:
					answer = self.AnsBase[1]
			else:
				answer = "Unknown scope."

		elif a1 in ("global", "глобальный"):
			a2 = body[body.lower().find(a1) + len(a1):].strip()

			def get_global_stats(source_):
				x, y = 0, 0
				for conf in Chats.keys():
					with self.db(conf) as db:
						db("SELECT * FROM talkers WHERE jid=?", (source_,))
						row = db.fetchone()
					if row:
						x += row[2]; y += row[3]
				if x:
					return self.AnsBase[2] % (x, y, round(y / x, 1))
				return self.AnsBase[1]

			if a2 in ("mine", "мой"):
				source_ = get_source(source[1], source[2])
				answer  = get_global_stats(source_) if source_ else self.AnsBase[1]
			elif Chats[source[1]].isHere(a2):
				source_ = get_source(source[1], a2)
				answer  = get_global_stats(source_) if source_ else self.AnsBase[1]
			elif ls and isSource(ls[0]):
				answer = get_global_stats(ls[0].lower())
			else:
				glob = {}
				for conf in Chats.keys():
					with self.db(conf) as db:
						db("SELECT * FROM talkers WHERE (jid LIKE ? OR lastnick LIKE ?) ORDER BY msgs DESC",
						   (a2, a2))
						rows = db.fetchall()
					for x in rows:
						if x[0] in glob:        # Fix: has_key → in
							glob[x[0]][2] += x[2]; glob[x[0]][3] += x[3]
						else:
							glob[x[0]] = list(x)
				if glob:
					top = sorted(glob.values(), key=lambda x: x[2], reverse=True)[:10]
					lines = [self.AnsBase[0]]
					for i, x in enumerate(top, 1):
						avg = round(x[3] / x[2], 1) if x[2] else 0
						lines.append("%d. %s\t\t%d\t%d\t%s" % (i, x[1], x[2], x[3], avg))
					lines.append(self.AnsBase[3])
					answer = "\n".join(lines)
				else:
					answer = self.AnsBase[1]

		elif a1 in ("local", "локальный"):
			a2 = body[body.lower().find(a1) + len(a1):].strip()

			def get_local_stats(source_, conf):
				with self.db(conf) as db:
					db("SELECT * FROM talkers WHERE jid=?", (source_,))
					x = db.fetchone()
				if x:
					return self.AnsBase[2] % (x[2], x[3], round(x[3] / x[2], 1) if x[2] else 0)
				return self.AnsBase[1]

			if a2 in ("mine", "мой"):
				source_ = get_source(source[1], source[2])
				answer  = get_local_stats(source_, source[1]) if source_ else self.AnsBase[1]
			elif Chats[source[1]].isHere(a2):
				source_ = get_source(source[1], a2)
				answer  = get_local_stats(source_, source[1]) if source_ else self.AnsBase[1]
			elif ls and isSource(ls[0]):
				answer = get_local_stats(ls[0].lower(), source[1])
			else:
				with self.db(source[1]) as db:
					db("SELECT * FROM talkers WHERE (jid LIKE ? OR lastnick LIKE ?) ORDER BY msgs DESC",
					   (a2, a2))
					rows = db.fetchall()
				if rows:
					lines = [self.AnsBase[0]]
					for i, x in enumerate(rows[:10], 1):
						avg = round(x[3] / x[2], 1) if x[2] else 0
						lines.append("%d. %s\t\t%d\t%d\t%s" % (i, x[1], x[2], x[3], avg))
					lines.append(self.AnsBase[3])
					answer = "\n".join(lines)
				else:
					answer = self.AnsBase[1]
		else:
			answer = "Unknown command."
		Answer(answer, stype, source, disp)

	def calculate_talkers(self, stanza, isConf, stype, source, body, isToBs, disp):
		if isConf and stype == sBase[1] and source[2]:
			source_ = get_source(source[1], source[2])
			if source_:
				nick = source[2].strip()
				with self.db(source[1]) as db:
					db("SELECT * FROM talkers WHERE jid=?", (source_,))
					row = db.fetchone()
					if row:
						db("UPDATE talkers SET lastnick=?, msgs=?, words=? WHERE jid=?",
						   (nick, row[2] + 1, row[3] + len(body.split()), source_))
					else:
						db("INSERT INTO talkers VALUES (?,?,?,?)",
						   (source_, nick, 1, len(body.split())))
					db.commit()

	def init_talkers_base(self, conf):
		filename = chat_file(conf, self.TalkersFile)
		folder   = os.path.dirname(filename)
		if folder and not os.path.exists(folder):
			os.makedirs(folder, exist_ok=True)
		if not os.path.isfile(filename):
			with Database(filename) as db:
				db("CREATE TABLE IF NOT EXISTS talkers "
				   "(jid TEXT, lastnick TEXT, msgs INTEGER, words INTEGER)")
				db.commit()
		# Fix: ithr.Semaphore() → threading.Semaphore()
		self.TalkersDesc[conf] = threading.Semaphore()

	def edit_talkers_desc(self, conf):
		self.TalkersDesc.pop(conf, None)

	commands = ((command_talkers, "talkers", 2,),)

	handlers = (
		(init_talkers_base, "01si"),
		(edit_talkers_desc, "04si"),
		(calculate_talkers, "01eh"),
	)