# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "cron" # /code.py v.x6
#  Id: 27~5c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	CronFile = dynamic % "cdesc.db"

	CronDesc    = {}
	# Fix: itypes.Number() → AtomicNumber()
	CronCounter = AtomicNumber()

	AnsBase = (
		"Executing cron: %s",           # 0
		"No cron with id %d.",          # 1
		"Interval too short or repeats too few.",  # 2
		" (+%d more repeats hidden)",   # 3
		"Schedule:\n%s",                # 4
		"Body too long.",               # 5
		"Scheduled: %s",                # 6
		"No cron tasks.",               # 7
		"Cron tasks:\n%s",              # 8
		"Invalid date.",                # 9
	)

	def def_cron(self):

		# Fix: itypes.Number.reduce() → custom counter class below
		def exe_cron(command, instance, ls, repeat=()):
			inst = get_source(ls[1][1], ls[1][2])
			if inst == instance or (not inst or not instance):
				gt   = time.mktime(time.gmtime())
				rlen = len(repeat)
				if rlen == 1 and repeat[0] >= 360:
					Answer(self.AnsBase[0] % command, ls[0], ls[1], ls[3])
				if command in Cmds:
					Cmds[command].execute(*ls)
				if rlen == 2:
					seconds, repeats = repeat
					repeats -= 1
					if repeats > 0:
						new_repeat = (seconds, repeats)
						self.CronDesc[self.CronCounter.plus()] = (
							(seconds + gt), (command, instance, ls, new_repeat))

		while VarCache["alive"]:
			sleep(2)
			if self.name not in expansions:          # Fix: has_key → in
				break
			now = time.mktime(time.gmtime())
			for id, (date, ls) in list(self.CronDesc.items()):
				if now > date:
					if ls[0] in Cmds:               # Fix: has_key → in
						sThread("command(cron)", exe_cron, ls)
					del self.CronDesc[id]

	def add_cron(self, disp, ls, body, Te, source, stype, gt, answer, repeat, **etc):
		cmd = ls.pop(0).lower()
		if cmd in Cmds:                             # Fix: has_key → in
			if enough_access(source[1], source[2], Cmds[cmd].access):
				if ls:
					body = body[(body.lower().find(cmd) + len(cmd)):].strip()
				else:
					body = ""
				if len(body) <= 1024:
					instance = get_source(source[1], source[2])
					self.CronDesc[self.CronCounter.plus()] = (
						Te, (cmd, instance, (stype, source, body, get_disp(disp)), repeat))
					self.cdesc_save()
				else:
					answer = self.AnsBase[5]
			else:
				answer = "Access denied."
		else:
			answer = "Unknown command."
		return answer

	def command_cron(self, stype, source, body, disp):
		gt = time.gmtime()
		if body:
			ls = body.split()
			if len(ls) >= 2:
				arg0 = ls.pop(0).lower()
				# Fix: "стоп".decode("utf-8") → literal string
				if arg0 in ("stop", "стоп"):
					id = ls.pop(0)
					if isNumber(id):
						id = int(id)
						if id in self.CronDesc:
							if enough_access(source[1], source[2], 7):
								del self.CronDesc[id]
								self.cdesc_save()
								answer = "Done."
							else:
								date, ls_ = self.CronDesc[id]
								if ls_[1] == get_source(source[1], source[2]):
									del self.CronDesc[id]
									self.cdesc_save()
									answer = "Done."
								else:
									answer = "Access denied."
						else:
							answer = self.AnsBase[1] % id
					else:
						answer = "Invalid id."
				elif arg0 in ("cycled", "цикл"):    # Fix: decode → literal
					if len(ls) >= 3:
						Te = ls.pop(0)
						Tr = ls.pop(0)
						if isNumber(Te) and isNumber(Tr):
							Te, Tr = int(Te), int(Tr)
							if Te <= 240 and Tr > 4:
								answer = self.AnsBase[2]
							elif (59 < Te and Te * Tr <= 4147200) or \
							      enough_access(source[1], source[2], 7):
								t_ls   = [Te]
								# Fix: xrange → range
								for x in range(7):
									t_ls.append(t_ls[-1] + Te)
								Time   = time.mktime(gt)
								Te    += Time
								answer = self.AnsBase[4] % enumerated_list(
									[time.ctime(dt + Time) for dt in t_ls])
								if Tr > 8:
									answer += self.AnsBase[3] % (Tr - 8)
								repeat = (int(Te - Time), Tr)
								add    = self.add_cron
								answer = add(disp=disp, ls=ls, body=body, Te=Te,
								             source=source, stype=stype, gt=gt,
								             answer=answer, repeat=repeat)
							else:
								answer = self.AnsBase[5]
						else:
							answer = "Invalid numbers."
					else:
						answer = "Not enough arguments."
				elif arg0 in ("date", "дата"):      # Fix: decode → literal
					if len(ls) >= 2:
						date     = list(gt)
						Te_parts = ls.pop(0).split("&")
						date[6], date[7], date[8] = 0, 0, 0
						Time_str = Te_parts.pop(0).split(":")
						try:
							date[3] = int(Time_str.pop(0))
							date[4] = int(Time_str.pop(0)) if Time_str else 0
							date[5] = int(Time_str.pop(0)) if Time_str else 0
						except Exception:
							answer = "Invalid time format."
						else:
							Date = Te_parts.pop(0) if Te_parts else None
							if Date:
								Date_parts = Date.split(".")
								try:
									date[2] = int(Date_parts.pop(0))
									if Date_parts:
										date[1] = int(Date_parts.pop(0))
									if Date_parts:
										date[0] = int(Date_parts.pop(0))
								except Exception:
									answer = "Invalid date format."
							if "answer" not in locals():  # Fix: locals().has_key → in
								try:
									date_t = time.struct_time(date)
								except Exception:
									answer = "Invalid date."
								else:
									Time = time.mktime(gt)
									Te   = time.mktime(date_t)
									if Te > Time:
										if (59 < Te - Time <= 4147200) or \
										    enough_access(source[1], source[2], 7):
											repeat = ((Te - Time),)
											try:
												answer = self.AnsBase[6] % time.ctime(Te)
											except ValueError:
												answer = self.AnsBase[9]
											else:
												add    = self.add_cron
												answer = add(disp=disp, ls=ls, body=body,
												             Te=Te, source=source, stype=stype,
												             gt=gt, answer=answer, repeat=repeat)
										else:
											answer = self.AnsBase[5]
									else:
										answer = "Date is in the past."
					else:
						answer = "Not enough arguments."
				elif isNumber(arg0):
					Te = int(arg0)
					if (59 < Te <= 4147200) or enough_access(source[1], source[2], 7):
						repeat = (Te,)
						Te    += time.mktime(gt)
						answer = self.AnsBase[6] % time.ctime(Te)
						add    = self.add_cron
						answer = add(disp=disp, ls=ls, body=body, Te=Te,
						             source=source, stype=stype, gt=gt,
						             answer=answer, repeat=repeat)
					else:
						answer = self.AnsBase[5]
				else:
					answer = "Invalid argument."
			else:
				answer = "Not enough arguments."
		elif not self.CronDesc:
			answer = self.AnsBase[7]
		else:
			Time = time.mktime(gt)
			lines = []
			for id, (date, desc) in sorted(self.CronDesc.items()):
				if date > Time:
					lines.append("%d (%s) [%s]" % (id, desc[0], time.ctime(date)))
			answer = self.AnsBase[8] % enumerated_list(lines)
		Answer(answer, stype, source, disp)

	def start_cron(self):
		Name = "def_cron"
		# Fix: ithr.enumerate/kill → threading
		for thr in threading.enumerate():
			if thr.name.startswith(Name):
				# daemon threads can't be killed; mark via flag instead
				pass
		if initialize_file(self.CronFile, "({}, 0)"):
			try:
				cdesc, ccnt = eval(get_file(self.CronFile))
			except Exception:
				cdesc, ccnt = {}, 0
			Time = time.mktime(time.gmtime())
			for id in list(cdesc.keys()):
				date, ls = cdesc[id]
				if Time > date:
					del cdesc[id]
				elif len(ls[3]) == 2:
					command, instance, ls__, repeat = ls
					seconds, repeats = repeat
					# repeats stored as int, keep as int
					cdesc[id] = (date, (command, instance, ls__, (seconds, repeats)))
			self.CronDesc.update(cdesc)
			# Fix: CronCounter.__init__(ccnt) → reset via internal value
			self.CronCounter._val = int(ccnt)
		composeThr(self.def_cron, Name).start()

	def cdesc_save(self, conf=None):
		if not conf:
			cdesc = {}
			for id, (date, ls) in self.CronDesc.items():
				command, instance, ls__, repeat = ls
				# repeats already int in Python 3
				repeat_save = (repeat[0], int(repeat[1])) if len(repeat) == 2 else repeat
				stype, source, body, disp_ = ls__
				source = (str(source[0]), source[1], source[2])
				cdesc[id] = (date, (command, instance, (stype, source, body, disp_), repeat_save))
			cat_file(self.CronFile, str((cdesc, int(self.CronCounter.value()))))

	commands = ((command_cron, "cron", 5,),)

	handlers = (
		(start_cron, "02si"),
		(cdesc_save, "03si"),
	)