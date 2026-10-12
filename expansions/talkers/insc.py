# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

if DefLANG in ("RU", "UA"):
	AnsBase_temp = tuple([line for line in (
		"\n[№][Юзер][Фраз][Слов][Коэф.]", # 0
		"Нет статистики.", # 1
		"\n[Фраз][Слов][Коэф.]\n%d\t%d\t%s", # 2
		"\n*! Поиск в базе произведён по ключу." # 3
	)])
