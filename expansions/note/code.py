# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "note" # /code.py v.x8
#  Id: 22~7c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		# Fix: check_sqlite() → tidak ada di Nexus, SQLite built-in
		expansion.__init__(self, name)

	NoteFile = dynamic % "notepad.db"

	AnsBase = (
		"Notepad is empty.",         # 0
		"Note too long (max 512).",  # 1
		"Invalid argument.",         # 2
		"Notepad is full (16 lines).", # 3
		"Done.",                     # 4  (generic ok)
		"Line is empty.",            # 5
		"Your notes:\n",             # 6
		"Saved to line %s.",         # 7
		"Line already empty.",       # 8
	)

	def command_note(self, stype, source, body, disp):
		source_ = get_source(source[1], source[2])
		if not source_:
			return Answer(self.AnsBase[2], stype, source, disp)

		if body:
			ls   = body.split()
			arg0 = ls.pop(0).lower()
			# Fix: "чисть".decode("utf-8") → literal
			if arg0 in ("clear", "чисть"):
				with Database(self.NoteFile) as db:
					db("SELECT * FROM note WHERE jid=?", (source_,))
					row = db.fetchone()
					if row:
						db("DELETE FROM note WHERE jid=?", (source_,))
						db.commit()
						answer = self.AnsBase[4]
					else:
						answer = self.AnsBase[0]
			elif ls:
				if arg0 == "+":
					body = body[2:].lstrip()
					if len(body) <= 512 or enough_access(source[1], source[2], 7):
						date = strfTime(local=False)
						with Database(self.NoteFile) as db:
							db("SELECT * FROM note WHERE jid=?", (source_,))
							row = db.fetchone()
							if row:
								# Fix: itypes.Number() → enumerate, xrange → range
								answer = self.AnsBase[3]
								for numb, val in enumerate(row):
									if numb == 0:
										continue
									if not val:
										db("UPDATE note SET line_%d=? WHERE jid=?" % numb,
										   ("[%s] %s" % (date, body), source_))
										db.commit()
										answer = self.AnsBase[7] % str(numb)
										break
							else:
								# Fix: xrange → range
								placeholders = ",".join(["?" for _ in range(17)])
								vals = (source_, "[%s] %s" % (date, body)) + ("",) * 15
								db("INSERT INTO note VALUES (%s)" % placeholders, vals)
								db.commit()
								answer = self.AnsBase[4]
					else:
						answer = self.AnsBase[1]
				elif arg0 in ("-", "*"):
					numb = ls.pop(0)
					if isNumber(numb):
						numb = int(numb)
						if 1 <= numb <= 16:       # Fix: range(1,17) → range check
							with Database(self.NoteFile) as db:
								db("SELECT * FROM note WHERE jid=?", (source_,))
								row = db.fetchone()
								if row:
									if arg0 == "*":
										answer = row[numb] if row[numb] else self.AnsBase[5]
									elif not row[numb]:
										answer = self.AnsBase[8]
									else:
										db("UPDATE note SET line_%d=? WHERE jid=?" % numb,
										   ("", source_))
										db.commit()
										answer = self.AnsBase[4]
								else:
									answer = self.AnsBase[0]
						else:
							answer = self.AnsBase[2]
					else:
						answer = "Invalid number."
				else:
					answer = self.AnsBase[2]
			else:
				answer = self.AnsBase[2]
		else:
			with Database(self.NoteFile) as db:
				db("SELECT * FROM note WHERE jid=?", (source_,))
				row = db.fetchone()
			if row:
				notes = []
				for numb, line in enumerate(row):
					if numb and line:
						notes.append("Line[%d] %s" % (numb, line))
				if notes:
					answer = self.AnsBase[6] + "\n".join(notes)
					if stype == sBase[1]:
						Message(source[0], answer, disp)
						answer = "Sent to PM."
				else:
					with Database(self.NoteFile) as db:
						db("DELETE FROM note WHERE jid=?", (source_,))
						db.commit()
					answer = self.AnsBase[0]
			else:
				answer = self.AnsBase[0]
		Answer(answer, stype, source, disp)

	def init_note_file(self):
		# Selalu pastikan tabel ada, terlepas dari apakah file .db sudah ada
		# (file kosong tanpa tabel bisa terjadi dari versi lama)
		cols = ", ".join("line_%d TEXT" % n for n in range(1, 17))
		with Database(self.NoteFile) as db:
			db("CREATE TABLE IF NOT EXISTS note (jid TEXT, %s)" % cols)
			db.commit()

	commands = ((command_note, "note", 2,),)

	handlers = ((init_note_file, "00si"),)