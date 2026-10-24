import sqlite3

# Шаг 1: Подключаемся к нашей созданной пещере данных
connection = sqlite3.connect('sitw_cave.db')
cursor = connection.cursor()

# Твои кастомные вводные данные из ночной сессии
user_name = "Брюс"
my_assistant = "Альфред" # Здесь ты можешь написать любое имя (хоть Джарвис, хоть Плюша)

print(f"[SITW Onboarding]: Запускаем органический протокол для пользователя {user_name}...")

# Шаг 2: Записываем Лидера и его Напарника в базу данных
cursor.execute("""
INSERT INTO users (username, assistant_name, current_exp, current_level)
VALUES (?, ?, 0, 1);
""", (user_name, my_assistant))

# Шаг 3: Сохраняем изменения в монолите
connection.commit()

# Шаг 4: Вытаскиваем данные обратно для проверки связи
cursor.execute("SELECT username, assistant_name, current_level FROM users WHERE username = ?;", (user_name,))
result = cursor.fetchone()

print(f"[SITW Onboarding]: Данные успешно синхронизированы!")
print(f"[SITW Core]: Лидер: {result[0]} | Напарник: {result[1]} | Уровень: {result[2]}")

# Шаг 5: Безопасно закрываем шлюзы
connection.close()
