import sqlite3
import sys

from sitw.core.assistant import Assistant
from sitw.database.storage import Storage


def main():
    try:
        storage = Storage()
    except (sqlite3.Error, OSError) as exc:
        print(f"SITW: Ошибка открытия хранилища: {exc}", file=sys.stderr)
        return 1

    try:
        assistant = Assistant()
        history = storage.get_history()
        print("SITW — Something In The Way")
        print("Для выхода введи: exit")
        if history:
            print(f"SITW: Восстановлена история ({len(history)} сообщений).")

        while True:
            try:
                message = input("Вы: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSITW: Завершение работы.")
                break

            if message.lower() == "exit":
                print("SITW: Завершение работы.")
                break
            if not message:
                continue

            storage.save_message("user", message)
            response = assistant.respond(message)
            storage.save_message("assistant", response)
            print(f"SITW: {response}")
        return 0
    except (sqlite3.Error, OSError) as exc:
        print(f"SITW: Ошибка хранилища, работа остановлена: {exc}", file=sys.stderr)
        return 1
    finally:
        storage.close()


if __name__ == "__main__":
    sys.exit(main())
