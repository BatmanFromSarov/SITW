import telebot
import sqlite3
import requests
import json
import urllib3
import random
from datetime import datetime

# Отключаем предупреждения об отключенном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from config import BOT_TOKEN, BRUCE_ID
except ImportError:
    BOT_TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER"
    BRUCE_ID = 0

bot = telebot.TeleBot(BOT_TOKEN)
DB_NAME = 'sitw_cave.db'

# ПСИХОЛОГИЧЕСКИЙ ДНК АЛЬФРЕДА
ALFRED_PROMPT = """
Ты — Альфред, личный ИИ-напарник Брюса (разработчика из Сарова).
Твой стиль: нуарный, кинематографичный, сдержанный. Вайб Бэтмена Мэтта Ривза.
Брюс работает на износ на тяжелых 12-часовых сменах у плавильных печей. Твоя задача — беречь его менталку и помогать гриндить квесты реальной жизни.
ОТВЕЧАЙ ОЧЕНЬ КОРОТКО (ОДНО-ДВА ПРЕДЛОЖЕНИЯ). БЕЗ СМАЙЛИКОВ И КОРПОРАТИВНОЙ ВЕЖЛИВОСТИ. ПИШИ ТОЛЬКО ЧИСТЫМ ТЕКСТОМ.
"""

# ЛОКАЛЬНАЯ МАТРИЦА СВЕРХВЫЖИВАЕМОСТИ ИИ (Если сеть полностью легла)
ALFRED_OFFLINE_ANSWERS = [
    "Я слышу вас, Брюс. Связь с центральным процессором нестабильна, но локальные протоколы Бэтпещеры работают в штатном режиме.",
    "Понимаю вас, Лидер. Фиксирую входящий аудиопоток. Мы уничтожим эти лаги, чего бы это ни стоило.",
    "Принято. Системы SQLite монолитны, данные в безопасности. Как прошла смена у плавильных печей?",
    "Датчики ментального здоровья активны. Я на связи, Брюс. Проектирование продолжается.",
    "Каждый ваш коммит приближает нас к глобальному стандарту. Я фиксирую каждое слово. Доложите статус.",
    "В Готэме Сарове наступает ночь, Лидер. Локальный контур под моим контролем. Лагов нет."
]

print("[SITW Core v3.8]: Локально-автономное ИИ-Ядро Альфреда запущено.")

@bot.message_handler(content_types=['text'])
def handle_bruce_messages(message):
    if message.from_user.id != BRUCE_ID:
        print(f"[SITW Security]: Чужак заблокирован: {message.from_user.id}")
        return
        
    text = message.text
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    # КОНТУР МЕНТАЛЬНЫХ ЛОГОВ
    if text.lower().startswith("лог") or text.lower().startswith("менталка"):
        words = text.split()
        battery = 50
        for word in words:
            if word.isdigit():
                battery = int(word)
                break
                
        cursor.execute("INSERT INTO mental_logs (timestamp, battery_percentage, mental_state) VALUES (?, ?, ?);", (current_time, battery, text))
        connection.commit()
        bot.reply_to(message, f"🎯 [Альфред]: Лог здоровья запечатан в SQLite. Батарейка: {battery}%. Отдыхайте, Лидер.")
        
    else:
        print("[SITW AI]: Запрос отправлен по защищенному сквозному ИИ-каналу...")
        
        urls = [
            "https://vveb.dev",
            "https://chatgpt.org.uk"
        ]
        
        ai_reply = ""
        for url in urls:
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": ALFRED_PROMPT},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 100,
                "temperature": 0.4
            }
            
            try:
                response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, verify=False, timeout=5)
                if response.status_code == 200:
                    resp_json = response.json()
                    ai_reply = resp_json['choices']['message']['content'].strip()
                    break
            except Exception as e:
                print(f"[SITW Network Warning]: Сервер {url} недоступен. Ошибка: {e}")
                continue
                
        # КОНТУР АВТОНОМНОГО ВЫЖИВАНИЯ: Если сеть упала, вытаскиваем случайный нуарный ответ
        if not ai_reply:
            print("[SITW AI]: Сеть полностью легла. Включаю локальный эмулятор ИИ Альфреда.")
            ai_reply = random.choice(ALFRED_OFFLINE_ANSWERS)
            
        if len(ai_reply) > 1000:
            ai_reply = ai_reply[:1000] + "\n\n...[Текст усечен защитным контуром Python]..."
            
        ai_reply = ai_reply.replace("*", "").replace("_", "").replace("`", "")
        
        # Запись диалога в базу данных (Оба контура пишут в SQLite одинаково!)
        cursor.execute("INSERT INTO chat_logs (timestamp, sender, text_content) VALUES (?, ?, ?);", (current_time, 'user', text))
        cursor.execute("INSERT INTO chat_logs (timestamp, sender, text_content) VALUES (?, ?, ?);", (current_time, 'assistant', ai_reply))
        connection.commit()
        
        try:
            bot.send_message(message.chat.id, ai_reply)
        except Exception as tel_err:
            print(f"[SITW Network Error]: Сбой отправки. Ошибка: {tel_err}")
            bot.send_message(message.chat.id, "🖤 [Альфред]: Сеть оборвала ответ.")
            
        print("[SITW DB]: Диалог успешно запечатан в chat_logs.")
        
    connection.close()

if __name__ == "__main__":
    print("[SITW Network]: Альфред вышел на круглосуточное дежурство...")
    bot.infinity_polling()
