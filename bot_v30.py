import telebot

# Импортируем секретный токен из локального файла config.py
try:
    from config import BOT_TOKEN
except ImportError:
    # Заглушка на случай, если файла config.py нет (например, у других людей на GitHub)
    BOT_TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER"

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN)

print("[SITW Network]: Сетевой реактор v3.0 переведен в режим ожидания...")

if __name__ == "__main__":
    print("[SITW Network]: Запуск тестового пинга серверов Telegram...")
    try:
        bot_info = bot.get_me()
        print(f"[SITW Network]: Связь установлена! Бот @{bot_info.username} на связи.")
    except Exception as e:
        print(f"[SITW Network]: Ошибка подключения. Проверь токен. Код ошибки: {e}")
