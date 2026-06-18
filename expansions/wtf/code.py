# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "wtf" # /code.py v.x4
#  Id: 28~4c
#  Original © (2012-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		# Fix: check_sqlite() → tidak ada, SQLite built-in Python 3
		expansion.__init__(self, name)

	Base     = dynamic % "wtf.db"
	ChatBase = "wtf.db"

	AnsBase = (
		"Global definitions (%d):\n%s",        # 0
		"Local definitions (%d) [%s]:\n%s",    # 1
		"No definitions found.",               # 2
		"%s — %d mentions",                    # 3
		"Not found.",                           # 4
		"%s:\n%s\n— Added by %s (%s)",         # 5
		"'%s' not found.",                      # 6
		"Global: %d definitions.",             # 7
		"Local: %d definitions [%s].",         # 8
		"'%s' exists globally, can't override.", # 9
		"No room context.",                    # 10
		"\n",                                  # -1 (separator)
	)

	def _db(self, path):
		return Database(path)

	def _chat_db_path(self, conf):
		return chat_file(conf, self.ChatBase)

	def command_wtf(self, stype, source, body, disp):
		if not body:
			ls = []
			with self._db(self.Base) as db:
				db("SELECT name FROM wtf ORDER BY name")
				defs = db.fetchall()
			if defs:
				ls.append(self.AnsBase[7] % len(defs))
			if source[1] in Chats:              # Fix: has_key → in
				with self._db(self._chat_db_path(source[1])) as db:
					db("SELECT name FROM wtf ORDER BY name")
					defs = db.fetchall()
				if defs:
					ls.append(self.AnsBase[8] % (len(defs), source[1]))
			answer = (self.AnsBase[-1] + "\n".join(ls)) if ls else self.AnsBase[2]
			return Answer(answer, stype, source, disp)

		ls   = body.split(None, 1)
		arg0 = ls.pop(0).lower()

		# Fix: all .decode("utf-8") → literals
		if arg0 in ("all", "всё"):
			parts = []
			with self._db(self.Base) as db:
				db("SELECT name FROM wtf ORDER BY name")
				defs = db.fetchall()
			if defs:
				parts.append(self.AnsBase[0] % (
					len(defs), enumerated_list([r[0].title() for r in defs])))
			if source[1] in Chats:
				with self._db(self._chat_db_path(source[1])) as db:
					db("SELECT name FROM wtf ORDER BY name")
					defs = db.fetchall()
				if defs:
					parts.append(self.AnsBase[1] % (
						len(defs), source[1],
						enumerated_list([r[0].title() for r in defs])))
			answer = (self.AnsBase[-1] + "\n\n".join(parts)) if parts else self.AnsBase[2]

		elif arg0 in ("search", "искать"):
			if not ls:
				return Answer("Provide a search term.", stype, source, disp)
			query  = ls[0].lower()
			found  = []
			with self._db(self.Base) as db:
				db("SELECT name, data FROM wtf ORDER BY name")
				for name, data in db.fetchall():
					n = data.lower().count(query)
					if n or query in name or name in query:
						found.append(self.AnsBase[3] % (name.title(), n))
			if source[1] in Chats:
				with self._db(self._chat_db_path(source[1])) as db:
					db("SELECT name, data FROM wtf ORDER BY name")
					for name, data in db.fetchall():
						n = data.lower().count(query)
						if n or query in name or name in query:
							found.append(self.AnsBase[3] % (name.title(), n))
			answer = (self.AnsBase[-1] + enumerated_list(found)) if found else self.AnsBase[4]

		else:
			term   = body.lower()
			answer = None
			with self._db(self.Base) as db:
				db("SELECT * FROM wtf WHERE name=?", (term,))
				row = db.fetchone()
			if row:
				answer = self.AnsBase[5] % (row[0].title(), row[1], row[2], row[3])
			if source[1] in Chats and not answer:
				with self._db(self._chat_db_path(source[1])) as db:
					db("SELECT * FROM wtf WHERE name=?", (term,))
					row = db.fetchone()
				if row:
					answer = self.AnsBase[5] % (row[0].title(), row[1], row[2], row[3])
			if not answer:
				answer = self.AnsBase[6] % term
		Answer(answer, stype, source, disp)

	sep = "="

	def addDef(self, base, name, data, nick):
		with self._db(base) as db:
			db("SELECT date FROM wtf WHERE name=?", (name,))
			exists = db.fetchone()
			if data:
				if exists:
					db("UPDATE wtf SET data=?, nick=?, date=? WHERE name=?",
					   (data, nick, time.asctime(), name))
				else:
					db("INSERT INTO wtf VALUES (?,?,?,?)",
					   (name, data, nick, time.asctime()))
				db.commit()
				return "Done."
			elif exists:
				db("DELETE FROM wtf WHERE name=?", (name,))
				db.commit()
				return "Done."
			else:
				return self.AnsBase[6] % name

	def command_def(self, stype, source, body, disp):
		if not body:
			return Answer("Provide a definition.", stype, source, disp)

		ls   = body.split(None, 1)
		arg0 = ls.pop(0).lower()

		# Fix: decode → literal
		if arg0 in ("globally", "глобально"):
			if not enough_access(source[1], source[2], 7):
				return Answer("Access denied.", stype, source, disp)
			if ls and self.sep in ls[0]:
				parts      = ls[0].split(self.sep, 1)
				name, data = parts[0].rstrip().lower(), parts[1].lstrip()
				if name and len(name) <= 64:
					answer = self.addDef(self.Base, name, data, source[2])
				else:
					answer = "Invalid name."
			else:
				answer = "Use: def globally name=definition"
		elif source[1] in Chats:               # Fix: has_key → in
			if self.sep in body:
				parts      = body.split(self.sep, 1)
				name, data = parts[0].rstrip().lower(), parts[1].lstrip()
				if name and len(name) <= 64:
					with self._db(self.Base) as db:
						db("SELECT date FROM wtf WHERE name=?", (name,))
						exists = db.fetchone()
					if exists and data:
						answer = self.AnsBase[9] % name
					else:
						answer = self.addDef(
							self._chat_db_path(source[1]), name, data, source[2])
				else:
					answer = "Invalid name."
			else:
				answer = "Use: def name=definition"
		else:
			answer = self.AnsBase[10]
		Answer(answer, stype, source, disp)

	def init_wtf_base(self):
		# Selalu ensure table ada — file .db kosong tanpa tabel bisa terjadi
		with self._db(self.Base) as db:
			db("CREATE TABLE IF NOT EXISTS wtf "
			   "(name TEXT, data TEXT, nick TEXT, date TEXT)")
			db.commit()

	def init_local_wtf_base(self, conf):
		filename = self._chat_db_path(conf)
		folder   = os.path.dirname(filename)
		if folder and not os.path.exists(folder):
			os.makedirs(folder, exist_ok=True)
		with self._db(filename) as db:
			db("CREATE TABLE IF NOT EXISTS wtf "
			   "(name TEXT, data TEXT, nick TEXT, date TEXT)")
			db.commit()

	commands = (
		(command_wtf, "wtf", 2,),
		(command_def, "def", 4,),
	)

	handlers = (
		(init_wtf_base,       "00si"),
		(init_local_wtf_base, "01si"),
	)