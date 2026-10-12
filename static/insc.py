# Porting Python3 by: paijo.ahmad@jabber.ru
# -*- coding: utf-8 -*-
if DefLANG in ("RU", "UA"):
	AnsBase = (
		"Данная команда доступна исключительно в конференциях.", # 0
		"Данная команда подразумевает использование параметров.", # 1
		"Инвалид синтакс.", # 2
		"«%s» нет в списке конференций.", # 3
		"Сделано.", # 4
		"Слишком длинные параметры.", # 5
		"Нет такой команды.", # 6
		"Не могу.", # 7
		"Меня нет в этой конференции.", # 8
		"Тип указан не корректно.", # 9
		"Недостаточный доступ.", # 10
		"Ответ в привате.", # 11
		"№ %d. — %s", # 12
		"Команды «%s» (%s)", # 13
		"Процесса «%s»", # 14
		"При выполнении %s --> произошла ошибка!", # 15
		"Ошибку смотри по команде --> 'ошибка %d' (Крэшфайл --> %s)", # 16
		"Ошибку смотри по командам --> 'ошибка %d', 'sh cat %s'", # 17
		"%s[...]\n\n** Лимит %d знаков! Продолжение по команде «далее».", # 18
		"Команда '%s' сейчас недоступна!", # 19
		"Ошибка %s (%s) - конфа: «%s».", # 20
		"Ошибка %s (%s), полный выход из «%s».", # 21
		"Ошибка %s (%s), пришлось выйти из «%s».", # 22
		"Отказываюсь работать без прав!", # 23
		"Отключаю все функции до получения прав админа!", # 24
		"Получение прав...", # 25
		"Статускод '%s' в %s (%s). Осуществляю полный выход!", # 26
		"Помощь по команде «ХЕЛП» (последнее действие - %s)", # 27
		"Клиент «%s» упал!", # 28
		"JID «%s» используется в другом клиенте! (отключаю его)", # 29
		"Это не число.", # 30
		"📋 Алиасы отключены.", # 31
		"❌ Недостаточно прав для этой команды.", # 32
		"❌ Неверный синтаксис алиаса.", # 33
		"❌ Неверный синтаксис условия.", # 34
		"❌ Слишком много условий (максимум 8).", # 35
		"❌ Атрибуты, условия, клаузы и флаги должны быть одной длины.", # 36
		"❌ Атрибуты и условия должны быть одной длины.", # 37
		"ℹ️ Для этой макрокоманды нет справки.", # 38
		"ℹ️ Алиас «%s» не найден.", # 39
		"Ростер включён.", # 40
		"Ростер отключён.", # 41
		"❌ Укажите поисковый запрос.", # 42
		"❌ Укажите определение.", # 43
		"❌ Нет запроса.", # 44
		"❌ Это не чат.", # 45
		"❌ Использование: botstatus <room|here|everywhere> <state> <text>", # 46
		"📤 Покинул %s: %s (%s)", # 47
		"❌ Команда '%s' сейчас недоступна!", # 48
		"❌ Отказано в доступе.", # 49
		"📡 Соединение потеряно: %s", # 50
	)
else:
	AnsBase = (
		"Only works in a room.", # 0
		"This one takes arguments.", # 1
		"Syntax looks off.", # 2
		"No '%s' in my chats list.", # 3
		"Done.", # 4
		"Those arguments are too long.", # 5
		"No such command.", # 6
		"Nope, can't.", # 7
		"I'm not in that room.", # 8
		"Bad type.", # 9
		"You need a higher access level.", # 10
		"Check your private messages.", # 11
		"# %d. - %s", # 12
		"command '%s' (%s)", # 13
		"process '%s'", # 14
		"Running %s hit an error!", # 15
		"Run 'excinfo %d' to see the error (crashfile: %s)", # 16
		"Run 'excinfo %d' or 'sh cat %s' to see the error", # 17
		"%s[...]\n\n** %d char limit. Type 'more' for the rest.", # 18
		"'%s' is unavailable right now.", # 19
		"Error %s (%s) in room '%s'.", # 20
		"Error %s (%s), fully leaving '%s'.", # 21
		"Error %s (%s), I left '%s'.", # 22
		"Can't run without admin rights.", # 23
		"Turning everything off until I'm admin.", # 24
		"Getting admin rights...", # 25
		"Status code '%s' in %s (%s). Full leave!", # 26
		"Type 'HELP' for more (last action: %s)", # 27
		"Client '%s' fell over!", # 28
		"JID '%s' is in use elsewhere, disconnecting it.", # 29
		"That's not a number.", # 30
		"📋 Aliases are disabled.", # 31
		"❌ You don't have access to that.", # 32
		"❌ Invalid alias syntax.", # 33
		"❌ Invalid condition syntax.", # 34
		"❌ Too many conditions (max 8).", # 35
		"❌ Attributes, conditions, clauses and flags must have the same length.", # 36
		"❌ Attributes and conditions must have the same length.", # 37
		"ℹ️ No help stored for this macro.", # 38
		"ℹ️ No alias called '%s'.", # 39
		"Roster on.", # 40
		"Roster off.", # 41
		"❌ Provide a search term.", # 42
		"❌ Provide a definition.", # 43
		"❌ No query.", # 44
		"❌ Not in a chat.", # 45
		"❌ Usage: botstatus <room|here|everywhere> <state> <text>", # 46
		"📤 Left %s: %s (%s)", # 47
		"❌ '%s' is unavailable right now.", # 48
		"❌ Access denied.", # 49
		"📡 Connection lost: %s", # 50
	)