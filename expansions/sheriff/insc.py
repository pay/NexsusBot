# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

# exp_name = "sheriff" # /insc.py — ported to Python 3

if DefLANG in ("RU", "UA"):
	# Fix: tuple([line ...]) → literal strings
	AnsBase_temp = (
		"слишком длинный ник. (%d - предел)",           # 0
		"запрещённый ник.",                             # 1
		"пробелы по краям ников - запрещены.",          # 2
		"нецензурный ник.",                             # 3
		"нельзя рекламить.",                            # 4
		"нецензурные высказывания.",                    # 5
		"слишком длинный пост.",                        # 6
		"используй нижний регистр.",                    # 7
		"нецензурный статус.",                          # 8
		"слишком длинный статус.",                      # 9
		"%s: бан после %d киков.",                      # 10
		"%s: нарушитель.",                              # 11
		"%s: антивайп.",                                # 12
		"презенс-флуд.",                                # 13
		"Опаньки! Ты заработал девойс. Осталось %s.",  # 14
		"флуд.",                                        # 15
		"%s лишение голоса на %d секунд.",              # 16
		"%s авторизация.",                              # 17
		"Чтобы получить голос %s, у тебя три попытки.", # 18
		"напиши: «сезам откройся» (без кавычек)\t\t|\tсезам откройся\n"
		"напиши: «я не бот» (без кавычек)\t\t\t|\tя не бот\n"
		"напиши: вторую букву русского алфавита\t\t|\tб\n"
		"напиши: шестую букву русского алфавита\t\t|\tе\n"
		"реши: семь + 121 = ? (ответ числом)\t\t|\t128\n"
		"реши: три + 253 = ? (ответ числом)\t\t\t|\t256\n"
		"напиши: столицу Испании\t\t\t\t\t|\tМадрид\n"
		"напиши: столицу России\t\t\t\t\t\t|\tМосква\n"
		"напиши: столицу Франции\t\t\t\t\t|\tПариж\n"
		"напиши: столицу Италии\t\t\t\t\t\t|\tРим",    # 19
		"%s: авторизация пройдена.",                    # 20
		"Тест пройден!",                                # 21
		"%s: не прошел авторизацию.",                   # 22
		"Неправильнй ответ!",                           # 23
		"\nКонфигурация cлужбы безопасности:\nЗапрет пробелов на концах ника: ", # 24
		"включена",                                     # 25
		"отключена",                                    # 26
		"\nМаксимальная длина ника: %d\nЗащита от вайпа: ",        # 27
		"\nНомер кика за которым следует бан: %d\nАвторизация: ",  # 28
		"\nЛояльность: %d\nАнтиреклама: ",              # 29
		"\nВремя девойса (в секундах): %d\nАнтимат: ",  # 30
		"\nМаксимальная длина сообщения: %d\nАнтикапс: ", # 31
		"\nМаксимальная длина презенса: %d\nРежим Спарты: ", # 32
		"",                                             # 33
		"Сервер в белом списке.",                       # 34
		"Сервера нет в дополнительном белом списке.",   # 35
		"Это не сервер."                                # 36
	)
	# Fix: "\s" → r"\s" (raw string)
	Obscene = r"(?:бляд|\sблят|\sбля\s|\sблять\s|\sплять\s|хуй|\sибал|\sебал|\sхуи|хуител|хуя|\sхую|\sхуе|\sахуе|\sохуе|хуев|хер|\sпох\s|\sнах\s|писд|пизд|рizd|\sпздц\s|\sеб|\sепана\s|\sепать\s|\sипать\s|\sвыепать\s|\sибаш|\sуеб|проеб|праеб|приеб|съеб|взъеб|взьеб|въеб|вьеб|выебан|перееб|недоеб|долбоеб|долбаеб|\sниибац|\sнеебац|\sнеебат|\sниибат|\sпидар|\sрidаr|\sпидар|\sпидор|педор|пидор|пидарас|пидараз|\sпедар|педри|пидри|\sзаеп|\sзаип|\sзаеб|ебучий|ебучка\s|епучий|епучка\s|\sзаиба|заебан|заебис|\sвыеб|выебан|\sпоеб|\sнаеб|\sнаеб|сьеб|взьеб|вьеб|\sгандон|\sгондон|пахуи|похуис|\sманда\s|мандав|залупа|\sзалупог)"

else:
	AnsBase_temp = (
		"too long nickname. (%d - limit)",              # 0
		"forbidden nickname.",                          # 1
		"spaces at the edges of nicknames - forbidden.", # 2
		"unprintable nickname.",                        # 3
		"advertising - forbidden.",                     # 4
		"unprintable message.",                         # 5
		"too long message.",                            # 6
		"use lowercase.",                               # 7
		"unprintable status message.",                  # 8
		"too long status message.",                     # 9
		"%s: ban after %d kicks.",                      # 10
		"%s: intruder.",                                # 11
		"%s: antiwipe.",                                # 12
		"presence flood.",                              # 13
		"Ooops! You have earned devoice. Left %s.",     # 14
		"flood.",                                       # 15
		"%s devoice in to %d seconds.",                 # 16
		"%s verification.",                             # 17
		"To get the voice %s, you have three attempts.", # 18
		"type: 'codename 47' (without quotes)\t\t|\tcodename 47\n"
		"type: 'I am not a bot' (without quotes)\t|\tI am not a bot\n"
		"type: second symbol of English alphabet\t|\tb\n"
		"type: sixth symbol of English alphabet\t\t|\te\n"
		"type answer: seven + 127 = ? (integer)\t\t|\t128\n"
		"type answer: three + 253 = ? (integer)\t\t|\t256\n"
		"type: capital of England\t\t\t\t\t|\tLondon\n"
		"type: capital of USA\t\t\t\t\t\t|\tWashington\n"
		"type: capital of France\t\t\t\t\t|\tParis\n"
		"type: capital of Russia\t\t\t\t\t|\tMoscow",  # 19
		"%s: verification passed.",                     # 20
		"Test passed!",                                 # 21
		"%s: verification missed.",                     # 22
		"Wrong answer!",                                # 23
		"\nConfiguration of security service:\nForbid of the spaces on the edges of nickname: ", # 24
		"enabled ",                                     # 25
		"disabled ",                                    # 26
		"\nMax nickname length: %d\nAntiwipe: ",        # 27
		"\nNumber of the kick, after that ban follows: %d\nVerification: ", # 28
		"\nLoyalty: %d\nAntiаdvertising: ",             # 29
		"\nDevoice-time (seconds): %d\nAntiobscene: ",  # 30
		"\nMaximum length of message: %d\nAnticaps: ",  # 31
		"\nMaximum length of presence: %d\nSparta mode: ", # 32
		"",                                             # 33
		"Server already in the white list.",            # 34
		"Server not in extra white list.",              # 35
		"This is not a server."                         # 36
	)
	# Fix: "\s" → r"\s" (raw string)
	Obscene = r"(?:\sfuck\s|\sshit\s|\sbitch\s|\sfaggot\s|\scock\s|\scunt\s)"