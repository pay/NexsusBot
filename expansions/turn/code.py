# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "turn" # /code.py v.x3
#  Id: 21~3c
#  Original © (2011-2012) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	# Fix: .decode("utf-8") → literal strings (Python 3 str is unicode)
	TableRU = 'ёйцукенгшщзхъфывапролджэячсмитьбю.!"№;%:?*()_+/-=\\ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ.'
	TableFI = '`qwertyuiopåvasdfghjklöäzxcvbnm,.-½!"#¤%&*()_+.-=\\?QWERTYUIOPÅ^ASDFGHJKLÖÄZXCVBNM;:_'
	TableEN = '`qwertyuiop[]asdfghjkl;\'zxcvbnm,./!@#;%^&*()_+.-=\\~QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?'
	TableLA = (TableFI if DefLANG == "FI" else TableEN)

	del TableFI, TableEN

	TurnBase = {}

	def command_turn(self, stype, source, body, disp):

		def turn(conf, body):
			desc = {}
			for user in Chats[conf].get_users():
				if user.ishere:
					for app in ([user.nick + key for key in (":", ",", ">")] + [user.nick]):
						if app in body:
							marker = "*%s*" % (len(desc) + 1)
							desc[marker] = app
							body = body.replace(app, marker)
			turned = ""
			for smb in body:
				if smb in self.TableLA:
					turned += self.TableRU[self.TableLA.index(smb)]
				elif smb in self.TableRU:
					turned += self.TableLA[self.TableRU.index(smb)]
				else:
					turned += smb
			# Fix: sub_desc with dict
			for marker, original in desc.items():
				turned = turned.replace(marker, original)
			return turned

		answer = None
		if source[1] in Chats:                      # Fix: has_key → in
			if body:
				answer = "Turn->\n" + turn(source[1], body)
			else:
				source_ = get_source(source[1], source[2])
				if source_ and source_ in self.TurnBase.get(source[1], {}):  # Fix: has_key → in
					(Time, body) = self.TurnBase[source[1]].pop(source_)
					msg = "Turn->\n[%s] <%s>: %s" % (Time, source[2], turn(source[1], body))
					Message(source[1], msg, disp)
				else:
					answer = "Nothing to turn."
		else:
			answer = "Not in a room."
		if answer:                                   # Fix: locals().has_key → if answer
			Answer(answer, stype, source, disp)

	def collect_turnable(self, stanza, isConf, stype, source, body, isToBs, disp):
		if isConf and stype == sBase[1] and source[2]:
			source_ = get_source(source[1], source[2])
			if source_:
				self.TurnBase.setdefault(source[1], {})[source_] = (
					strfTime("%H:%M:%S", False), body)

	def init_turn_base(self, conf):
		self.TurnBase[conf] = {}

	def edit_turn_base(self, conf):
		self.TurnBase.pop(conf, None)

	commands = ((command_turn, "turn", 1,),)

	handlers = (
		(init_turn_base,    "01si"),
		(edit_turn_base,    "04si"),
		(collect_turnable,  "01eh"),
	)