import sqlite3
import subprocess

# Шаг 1: Входим в контур базы данных
connection = sqlite3.connect('sitw_cave.db')
cursor = connection.cursor()

# Квест, который мы хотим закрыть (в будущем эта строка будет прилетать из чата Telegram)
target_quest_title = "Пройти 2 быстрых урока по SQL"

print(f"[SITW Resolver v2.5]: Протокол закрытия контракта для задачи: '{target_quest_title}'...")

# Шаг 2: Проверяем, есть ли такой активный квест в базе
cursor.execute("SELECT quest_id, status FROM quests WHERE title = ?;", (target_quest_title,))
quest = cursor.fetchone()

if quest:
    quest_id, status = quest
    if status == 'active':
        # Шаг 3: Обновляем статус квеста на выполненный
        cursor.execute("UPDATE quests SET status = 'completed' WHERE quest_id = ?;", (quest_id,))
        connection.commit()
        print(f"[SITW Resolver v2.5]: Квест успешно переведен в статус [ВЫПОЛНЕНО].")
    else:
        print(f"[SITW Resolver v2.5]: Внимание. Этот квест уже был выполнен ранее.")
else:
    print(f"[SITW Resolver v2.5]: Критическая ошибка. Квест с таким названием не найден в базе.")

# Безопасно закрываем шлюз перед запуском следующего скрипта
connection.close()

# Шаг 4: Бесшовный сквозной вызов ядра! 
# Скрипт сам автоматически запускает твой прошлый математический движок v2.4 для перерасчета EXP
print("[SITW Resolver v2.5]: Инициирую сквозной перерасчет опыта...")
subprocess.run(["python", "engine_v24.py"])
