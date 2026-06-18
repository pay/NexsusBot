# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3 / slixmpp)
# exp_name = "alive_keeper" # /code.py v.x8
#  Original © (2011-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	def alive_keeper(self):
		while VarCache["alive"]:
			sleep(120)
			# Fix: ithr.getNames() → threading
			thr_names = [t.name for t in threading.enumerate()]
			for disp_str, client in list(Clients.items()):
				if not hasattr(client, "aKeeper"):
					client.aKeeper = AtomicNumber()   # Fix: itypes.Number() → AtomicNumber()
				if client.aKeeper.value() > 2:
					client.aKeeper = AtomicNumber()
					thrName = "%s-%s" % (sBase[13], disp_str)
					# Fix: ithr thread kill → tidak bisa kill thread di Python 3
					# cukup mulai reconnect jika belum ada
					if thrName not in thr_names:
						try:
							composeThr(connectAndDispatch, thrName, (disp_str,)).start()
						except Exception:
							delivery("Connection lost: %s" % disp_str)
				elif self.name in expansions:
					client.aKeeper.plus()
					# Ping via slixmpp xep_0199
					schedule_coro(_do_ping(disp_str), disp_str)
				else:
					return                            # Fix: ithr.ThrKill → return

	def conf_alive_keeper(self):
		while VarCache["alive"]:
			sleep(1800)  # 30 menit — sebelumnya 360 (6 menit), terlalu sering
			thr_names = [t.name for t in threading.enumerate()]  # Fix: ithr → threading
			for conf in list(Chats.values()):
				if not (online(conf.disp) and conf.IamHere):
					continue
				if not hasattr(conf, "aKeeper"):
					conf.aKeeper = AtomicNumber()     # Fix: itypes.Number() → AtomicNumber()
				if conf.aKeeper.value() > 2:
					conf.aKeeper = AtomicNumber()
					TimerName = "ejoin-%s" % conf.name
					if TimerName not in thr_names:
						try:
							composeTimer(180, conf.join, TimerName).start()
						except Exception:
							collectExc(composeTimer)
				elif self.name in expansions:
					conf.aKeeper.plus()
					# Ping room via send presence ke room/nick
					schedule_coro(_do_room_ping(conf.disp, conf.name, conf.nick), conf.disp)
				else:
					return                            # Fix: ithr.ThrKill → return

	def start_keepers(self):
		Name1 = "alive_keeper"
		Name2 = "conf_alive_keeper"
		# Fix: ithr.enumerate/kill → tidak bisa kill, thread lama akan stop sendiri
		# karena self.name tidak lagi in expansions setelah reload
		composeThr(self.alive_keeper,      Name1).start()
		composeThr(self.conf_alive_keeper, Name2).start()

	handlers = ((start_keepers, "02si"),)


# ── Helper coroutines untuk ping ──────────────────────────────

async def _do_ping(disp_str):
	"""Ping server via xep_0199."""
	client = Clients.get(disp_str)
	if not client:
		return
	try:
		server = client._nx_server
		await client.plugin["xep_0199"].send_ping(server, timeout=10)
		if hasattr(client, "aKeeper"):
			client.aKeeper = AtomicNumber()
	except Exception:
		pass


async def _do_room_ping(disp_str, room, nick):
	"""Ping room dengan send presence."""
	client = Clients.get(disp_str)
	if not client or not client.isConnected():
		return
	try:
		client.send_presence(
			pto="%s/%s" % (room, nick),
			pshow=sList[0],
			pstatus=Chats[room].status if room in Chats else DefStatus
		)
		if room in Chats and hasattr(Chats[room], "aKeeper"):
			Chats[room].aKeeper = AtomicNumber()
	except Exception:
		pass