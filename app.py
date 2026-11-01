import sqlite3
import sys

from sitw.core.assistant import Assistant
from sitw.core.backend import BackendCloseError, GenerationError, InvalidResponseError
from sitw.database.storage import Storage


def main():
    try:
        storage = Storage()
    except (sqlite3.Error, OSError) as exc:
        print(f"SITW: Ошибка открытия хранилища: {exc}", file=sys.stderr)
        return 1

    assistant = None
    status = 0
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
            try:
                response = assistant.respond(message)
            except GenerationError as exc:
                reason = (
                    "получен пустой или некорректный ответ"
                    if isinstance(exc, InvalidResponseError)
                    else "сбой backend"
                )
                print(
                    f"SITW: Не удалось сформировать ответ: {reason}. "
                    "Ваше сообщение сохранено. Работа остановлена.",
                    file=sys.stderr,
                )
                status = 1
                break
            storage.save_message("assistant", response)
            print(f"SITW: {response}")
    except (sqlite3.Error, OSError) as exc:
        print(f"SITW: Ошибка хранилища, работа остановлена: {exc}", file=sys.stderr)
        status = 1
    finally:
        try:
            if assistant is not None:
                try:
                    assistant.close()
                except BackendCloseError:
                    print("SITW: Ошибка освобождения ресурсов backend.", file=sys.stderr)
                    status = 1
        finally:
            try:
                storage.close()
            except (sqlite3.Error, OSError):
                print("SITW: Ошибка закрытия хранилища.", file=sys.stderr)
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
