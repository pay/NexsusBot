# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

if DefLANG in ("RU", "UA"):
	AnsBase_temp = tuple([line for line in (
		"\nВсего входов - %d\nВремя последнего входа - %s\nПоследняя роль - %s", # 0
		"\nВремя последнего выхода - %s\nПричина выхода - %s", # 1
		"\nНики: %s", # 2
		"Нет статистики.", # 3
		"«%s» сидит здесь - %s.", # 4
		"Ты провёл здесь - %s.", # 5
		"Здесь нет такого юзера." # 6
	)])
