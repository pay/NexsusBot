# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

if DefLANG in ("RU", "UA"):
	AnsBase_temp = tuple([line for line in (
		"Неверно указана единица измерения.", # 0
		"Oops...", # 1
		"Неверно указана категория." # 2
	)])
else:
	AnsBase_temp = (
		"Incorrect unit.", # 0
		"Oops...", # 1
		"Incorrect category." # 2
	)