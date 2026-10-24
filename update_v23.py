import sqlite3

# Шаг 1: Подключаемся к локальному монолиту
connection = sqlite3.connect('sitw_cave.db')
cursor = connection.cursor()

print("[SITW Core v2.3]: Контур обновления запущен.")

# Шаг 2: Создаем таблицу квестов quests
cursor.execute("""
CREATE TABLE IF NOT EXISTS quests (
    quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    quest_type TEXT NOT NULL, -- Daily, Main, Rescue
    exp_reward INTEGER NOT NULL,
    status TEXT DEFAULT 'active' -- active, completed
);
""")

# Шаг 3: Накатываем стартовые квесты в базу для Брюса
initial_quests = [
    ('Пройти 2 быстрых урока по SQL', 'Daily', 25, 'completed'),
    ('Собрать первый скрипт и материализовать файл базы данных', 'Main', 100, 'completed'),
    ('Развернуть репозиторий BatmanFromSarov и опубликовать DevLog', 'Main', 50, 'completed')
]

# Проверяем, если таблица пустая — заполняем её
cursor.execute("SELECT COUNT(*) FROM quests;")
if cursor.fetchone()[0] == 0:
    cursor.executemany("""
    INSERT INTO quests (title, quest_type, exp_reward, status)
    VALUES (?, ?, ?, ?);
    """, initial_quests)
    print("[SITW Core v2.3]: Стартовая карта квестов успешно загружена.")

# Шаг 4: Закрепляем транзакцию в сталь
connection.commit()

# Шаг 5: Выводим лог для контроля структуры
cursor.execute("SELECT title, quest_type, exp_reward, status FROM quests;")
all_quests = cursor.fetchall()

print("\n--- ТЕКУЩИЙ ЖУРНАЛ КВЕСТОВ В БАЗЕ ДАННЫХ ---")
for q in all_quests:
    status_icon = "🟢 [ВЫПОЛНЕНО]" if q[3] == 'completed' else "⚔️ [АКТИВЕН]"
    print(f"{status_icon} {q[0]} ({q[1]}-квест) | Награда: +{q[2]} EXP")

connection.close()
