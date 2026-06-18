# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3)
# exp_name = "game" # /code.py v.x2
#  Id: 26~2c
#  Original © (2011) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	# Fix: GameChrLS → definisikan langsung
	# Rock-Paper-Scissors-Lizard-Spock
	_chars = ("rock", "paper", "scissors", "lizard", "spock")

	# Fix: GameRules → definisikan langsung
	# Indeks 0-9 sesuai GameDesc value
	_rules = (
		"paper covers rock",        # 0
		"scissors cut paper",       # 1 -- rock crushes scissors? no: scissors[2] beats paper[1] -> idx1
		"rock crushes scissors",    # wait, let's map from GameDesc logic below
		"lizard eats paper",        # 3
		"spock smashes scissors",   # 4
		"lizard poisons spock",     # 5
		"scissors decapitate lizard", # 6
		"spock vaporizes rock",     # 7
		"rock crushes lizard",      # 8
		"paper disproves spock",    # 9 -- wait GameDesc[rock][paper]=9 means paper wins
	)

	# GameDesc[A][B] = rule_index means B beats A (bot chose A, user chose B → user wins)
	# Reconstructed from original indices:
	# rock(0) loses to: paper(1)→9, spock(3)→2  -- but original had GameChrLS[3]=lizard? let's fix
	# Original order likely: rock, paper, scissors, lizard, spock
	# GameDesc[rock]   = {paper:9, lizard:2}   rock loses to paper(9) & spock(?)
	# Let's just use standard RPSLS rules directly

	GameDesc = {
		"rock":     {"paper": "paper covers rock",      "spock": "spock vaporizes rock"},
		"paper":    {"scissors": "scissors cut paper",  "lizard": "lizard eats paper"},
		"scissors": {"rock": "rock crushes scissors",   "spock": "spock smashes scissors"},
		"lizard":   {"rock": "rock crushes lizard",     "scissors": "scissors decapitate lizard"},
		"spock":    {"paper": "paper disproves spock",  "lizard": "lizard poisons spock"},
	}

	AnsBase = (
		"Draw!",                    # 0
		"You win! %s.",             # 1
		"I win! %s.",               # 2
	)

	def command_game(self, stype, source, body, disp):
		if body:
			Char = body.lower().split()[0]
			if Char in self.GameDesc:
				# Fix: choice(dict.keys()) → choice(list(...))
				Char_2 = choice(list(self.GameDesc.keys()))
				Answer(Char_2, stype, source, disp)
				sleep(3.2)
				if Char == Char_2:
					answer = self.AnsBase[0]
				elif Char in self.GameDesc[Char_2]:
					# bot played Char_2, user played Char, Char beats Char_2
					answer = self.AnsBase[1] % self.GameDesc[Char_2][Char]
				else:
					# bot played Char_2, Char_2 beats Char
					answer = self.AnsBase[2] % self.GameDesc[Char][Char_2]
			else:
				answer = "Choose: %s" % ", ".join(self.GameDesc.keys())
		else:
			answer = "Rock-Paper-Scissors-Lizard-Spock!\nChoose: %s" % ", ".join(self.GameDesc.keys())
		Answer(answer, stype, source, disp)

	commands = ((command_game, "game", 2,),)