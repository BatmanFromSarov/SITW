import sqlite3

# Шаг 1: Входим в контур Бэтпещеры
connection = sqlite3.connect('sitw_cave.db')
cursor = connection.cursor()

print("[SITW Engine v2.4]: Математический процессор ядра запущен.")

# Шаг 2: Считаем сумму EXP за все выполненные квесты
cursor.execute("SELECT SUM(exp_reward) FROM quests WHERE status = 'completed';")
total_exp = cursor.fetchone()[0]

# Если квестов еще нет, ставим 0, чтобы код не упал
if total_exp is None:
    total_exp = 0

print(f"[SITW Engine v2.4]: Расчет окончен. Твой честный заработанный трофей: {total_exp} EXP.")

# Шаг 3: Обновляем данные Лидера в таблице users
# Мы закладываем простую логику: если EXP больше 100 — ты автоматически получаешь 2 уровень!
new_level = 1
if total_exp >= 100:
    new_level = 2

cursor.execute("""
UPDATE users 
SET current_exp = ?, current_level = ? 
WHERE username = 'Брюс';
""", (total_exp, new_level))

# Шаг 4: Запечатываем транзакцию
connection.commit()

# Шаг 5: Контрольный замер профиля
cursor.execute("SELECT username, current_exp, current_level FROM users WHERE username = 'Брюс';")
profile = cursor.fetchone()

print("\n--- ОБНОВЛЕННЫЙ ПРОФИЛЬ ЛИДЕРА В БАЗЕ ---")
print(f"👤 Пользователь: {profile[0]}")
print(f"⚡ Общий опыт: {profile[1]} EXP")
print(f"🏆 Текущий уровень: {profile[2]} LVL")

connection.close()
