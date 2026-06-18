# coding: utf-8

if DefLANG in ("RU", "UA"):
	AnsBase_temp = (
		"Напиши вопрос после команды.",                  # 0
		"⏳ AI таймаут — попробуй ещё раз.",             # 1
		"❌ llama-cli не найден. Проверь установку.",    # 2
		"❌ Модель не найдена:\n  %s",                  # 3
		"❌ Ошибка AI: %s",                             # 4
		"❌ Слишком длинный запрос (макс. %d символов).",# 5
		"🤖 AI обрабатывает запрос...",                  # 6
	)
else:
	AnsBase_temp = (
		"Write your question after the command.",        # 0
		"⏳ AI timeout — please try again.",             # 1
		"❌ llama-cli not found. Check installation.",   # 2
		"❌ Model not found:\n  %s",                    # 3
		"❌ AI error: %s",                              # 4
		"❌ Input too long (max %d characters).",        # 5
		"🤖 AI is processing...",                        # 6
	)
