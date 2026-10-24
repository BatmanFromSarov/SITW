import sqlite3
from datetime import datetime

# Шаг 1: Подключаемся к нашему оффлайн-бункеру данных
connection = sqlite3.connect('sitw_cave.db')
cursor = connection.cursor()

print("[SITW Core v2.6]: Контур логов активирован.")

# Шаг 2: Создаем таблицу Ментального здоровья
cursor.execute("""
CREATE TABLE IF NOT EXISTS mental_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    battery_percentage INTEGER NOT NULL,
    mental_state TEXT
);
""")

# Шаг 3: Создаем таблицу Болталки (Лог диалогов)
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_logs (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sender TEXT NOT NULL, -- user или assistant
    text_content TEXT NOT NULL
);
""")

# Шаг 4: Имитируем ночную запись — заносим твой реальный замер со смены!
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

cursor.execute("""
INSERT INTO mental_logs (timestamp, battery_percentage, mental_state)
VALUES (?, ?, ?);
""", (current_time, 10, "Пиковое выгорание. Самая тяжелая смена в цикле у плавильных печей."))

print("[SITW Core v2.6]: Таблицы 'mental_logs' и 'chat_logs' успешно выкованы.")
print("[SITW Core v2.6]: Реальный лог ночного тильта Лидера успешно запечатан в базу.")

# Шаг 5: Запечатываем транзакцию в сталь
connection.commit()

# Проверяем запись через вывод в терминал
cursor.execute("SELECT battery_percentage, mental_state FROM mental_logs ORDER BY log_id DESC LIMIT 1;")
last_log = cursor.fetchone()

print("\n--- ПОСЛЕДНЯЯ ЗАПИСЬ В ЖУРНАЛЕ ЗДОРОВЬЯ ---")
print(f"🔋 Заряд батарейки: {last_log[0]}%")
print(f"📝 Состояние: {last_log[1]}")

connection.close()
