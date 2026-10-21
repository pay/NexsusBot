# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru
# AnsBase untuk expansion "converter".
#
# Indeks:
#   0 Incorrect unit / Неверно указана единица измерения.
#   1 Oops... / Oops...
#   2 Incorrect category / Неверно указана категория.
#   3 Invalid number / Неверное число.
#   4 Unknown unit. Use 'convert %s' to list available units.
#   5 No unit info found for: %s
#   6 Usage: convert <category> <number> <from> <to>
#   7 Unknown category. Available: %s
#   8 Available categories: %s

if DefLANG in ("RU", "UA"):
	AnsBase_temp = tuple([line for line in (
		"Неверно указана единица измерения.", # 0
		"Oops...", # 1
		"Неверно указана категория.", # 2
		"Неверное число.", # 3
		"Неизвестная единица. Используйте 'convert %s' чтобы увидеть список единиц.", # 4
		"Информация об единицах не найдена для: %s", # 5
		"Использование: convert <категория> <число> <из> <в>", # 6
		"Неизвестная категория. Доступные: %s", # 7
		"Доступные категории: %s", # 8
	)])
else:
	AnsBase_temp = (
		"Incorrect unit.", # 0
		"Oops...", # 1
		"Incorrect category.", # 2
		"Invalid number.", # 3
		"Unknown unit. Use 'convert %s' to list available units.", # 4
		"No unit info found for: %s", # 5
		"Usage: convert <category> <number> <from> <to>", # 6
		"Unknown category. Available: %s", # 7
		"Available categories: %s", # 8
	)
