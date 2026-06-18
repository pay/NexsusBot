# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

if DefLANG in ("RU", "UA"):
	AnsBase_temp = tuple([line for line in (
		"Команда «%s» разрешена.", # 0
		"Команда «%s» запрещена.", # 1
		"Эта команда не может быть запрещена.", # 2
		"Нет запрещенных команд." # 3
	)])
else:
	AnsBase_temp = (
		"Command '%s' is allowed.", # 0
		"Command '%s' is forbidden.", # 1
		"This command can't be forbidden.", # 2
		"No forbidden commands." # 3
	)