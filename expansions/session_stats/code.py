# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "session_stats" # /code.py v.x6
#  Original © (2010-2012) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 by Nexsus Project 2026

import gc

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	def command_exc_info(self, stype, source, body, disp):
		answer = None
		if body:
			if isNumber(body):
				idx = int(body) - 1
				if 0 <= idx < len(VarCache["errors"]):
					try:
						exc = VarCache["errors"][idx]
						if isinstance(exc, bytes):
							try:
								exc = exc.decode("cp1251")
							except Exception:
								exc = exc.decode("utf-8", errors="replace")
						exc = str(exc)
						if stype == sBase[1]:
							Answer(AnsBase[11], stype, source, disp)
						Message(source[0], exc, disp)
					except Exception:
						answer = self.AnsBase[20]
				else:
					answer = self.AnsBase[21] % body
			else:
				answer = AnsBase[30]
		else:
			answer = self.AnsBase[22] % len(VarCache["errors"])
		if answer:
			Answer(answer, stype, source, disp)

	def command_botup(self, stype, source, body, disp):
		NowTime = time.time()
		answer  = self.AnsBase[15] % Time2Text(NowTime - Info["up"])
		if Info["alls"]:
			answer += self.AnsBase[16] % (
				Time2Text(NowTime - Info["sess"]),
				str(len(Info["alls"])),
				", ".join(sorted(Info["alls"]))
			)
		elif not OSList.windows:
			answer += self.AnsBase[17]
		Answer(answer, stype, source, disp)

	def command_session(self, stype, source, body, disp):
		NowTime = time.time()
		answer  = self.AnsBase[0]  % NxPid
		answer += self.AnsBase[1]  % Time2Text(NowTime - Info["up"])
		if Info["alls"]:
			answer += self.AnsBase[2] % Time2Text(NowTime - Info["sess"])
		answer += self.AnsBase[7]  % len(Chats)
		answer += self.AnsBase[3]  % Info["msg"].value()
		answer += self.AnsBase[4]  % Info["cmd"].value()
		answer += self.AnsBase[5]  % (Info["prs"].value(), Info["iq"].value())
		answer += self.AnsBase[6]  % (Info["omsg"].value(), Info["outiq"].value())

		total_users = sum(len(conf.get_nicks()) for conf in Chats.values())
		answer += self.AnsBase[8]  % total_users
		answer += self.AnsBase[10] % (len(VarCache["errors"]), Info["errors"].value())
		answer += self.AnsBase[11] % Info["cfw"].value()

		# Thread count
		n_threads = threading.active_count()
		answer += self.AnsBase[12] % (n_threads, n_threads)

		# CPU time
		try:
			answer += self.AnsBase[13] % os.times()[0]
		except Exception:
			pass

		# Memory
		mem = self._get_memory_kb()
		if mem:
			answer += self.AnsBase[14] % round(mem / 1024, 3)

		Answer(answer, stype, source, disp)

	def command_stats(self, stype, source, body, disp):
		if body:
			cmd = body.lower()
			if cmd in Cmds:
				answer = self.AnsBase[18] % (cmd, Cmds[cmd].numb.value(), len(Cmds[cmd].desc))
			else:
				answer = AnsBase[6]
		else:
			ls = []
			for cmd in Cmds.values():
				used = cmd.numb.value()
				if used:
					ls.append((used, len(cmd.desc), cmd.name))
			rows   = sorted(ls, reverse=True)
			answer = self.AnsBase[19] + "\n".join(
				"%d. %s - %d (%d)" % (n, name, used, desc)
				for n, (used, desc, name) in enumerate(rows, 1)
			)
		Answer(answer, stype, source, disp)

	def _get_memory_kb(self):
		try:
			import resource
			return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		except ImportError:
			pass
		try:
			# Windows fallback
			import psutil
			return psutil.Process(NxPid).memory_info().rss // 1024
		except Exception:
			pass
		try:
			with open("/proc/%d/status" % NxPid) as f:
				for line in f:
					if line.startswith("VmRSS:"):
						return int(line.split()[1])
		except Exception:
			pass
		return 0

	commands = (
		(command_exc_info, "excinfo",  8,),
		(command_botup,    "botup",    1,),
		(command_session,  "stat",     1,),
		(command_stats,    "comstat",  1,),
	)
