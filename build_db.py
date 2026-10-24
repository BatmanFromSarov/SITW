import sqlite3

# Шаг 1: Подключаемся к файлу базы данных (если его нет, он создастся сам)
connection = sqlite3.connect('sitw_cave.db')
cursor = connection.cursor()

print("[SITW Core]: Подключение к sitw_cave.db успешно выполнено.")

# Шаг 2: Создаем таблицу пользователей с контуром кастомного имени напарника
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    assistant_name TEXT DEFAULT 'Альфред',
    current_exp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1
);
""")

# Шаг 3: Сохраняем изменения и проверяем версию движка SQLite
connection.commit()
cursor.execute("SELECT sqlite_version();")
version = cursor.fetchone()[0]

print(f"[SITW Core]: Архитектура v2.1 запечатана. Таблица 'users' создана.")
print(f"[SITW Core]: Версия локального движка SQLite: {version}")

# Шаг 4: Закрываем соединение с бункером данных
connection.close()
