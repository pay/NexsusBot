# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2
# exp_name = "clear_stats" # /code.py v.x4
#  Id: 12~4c
#  Code © (2011) by WitcherGeralt [alkorgun@gmail.com]

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	def join_clear(self, conf, nick, instance, role, stanza, disp):
		if instance:
			for obj in Chats[conf].get_users():
				if obj.source == instance and not obj.ishere and obj.nick != nick:
					if Chats[conf].isHere(obj.nick):
						Chats[conf].desc.pop(obj.nick)

	def exit_clear(self, conf, nick, sbody, scode, disp):
		instance = get_source(conf, nick)
		if instance:
			delete = False
			for obj in Chats[conf].get_users():
				if obj.source == instance and obj.ishere:
					delete = True
					break
			if delete and Chats[conf].isHere(nick):
				Chats[conf].desc.pop(nick)

	def refresh_users_db(self):
		"""
		Dipanggil sekali setiap startup (~15s setelah READY, memberi waktu
		roster MUC lengkap diterima). Hapus baris users.db untuk
		(chat, jid) yang tidak lagi ada di room manapun yang diikuti bot —
		"refresh" agar data lama (user yang sudah keluar/lama) tidak
		menumpuk selamanya.
		"""
		def _do_cleanup():
			try:
				present = set()
				for conf, chat in Chats.items():
					for u in chat.get_users():
						if u.source:
							present.add((conf, u.source))

				rows = runDatabaseQuery("SELECT chat, jid FROM users")
				removed = 0
				for chat, jid in rows:
					if (chat, jid) not in present and chat in Chats:
						runDatabaseQuery(
							"DELETE FROM users WHERE chat=? AND jid=?",
							(chat, jid), set=True)
						removed += 1
				if removed:
					PrintInfo("users.db refreshed: %d stale entr%s removed" %
					          (removed, "y" if removed == 1 else "ies"))
			except Exception:
				exc_info_()

		composeTimer(15, _do_cleanup, "users-db-refresh").start()

	handlers = (
		(join_clear, "04eh"),
		(exit_clear, "05eh"),
		(refresh_users_db, "02si"),
	)
