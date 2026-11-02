import argparse
import math
import sqlite3
import sys

from sitw.core.assistant import Assistant
from sitw.core.backend import (
    BackendCloseError, GenerationError, InvalidResponseError,
    ModelUnavailableError, ResponseInterruptedError, ServerUnavailableError,
)
from sitw.core.ollama_backend import OllamaBackend
from sitw.database.storage import Storage


def positive_timeout(value):
    try:
        timeout = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Тайм-аут должен быть положительным числом.") from None
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("Тайм-аут должен быть положительным конечным числом.")
    return timeout


def positive_context_messages(value):
    try:
        limit = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Лимит контекста должен быть положительным целым числом.") from None
    if limit <= 0:
        raise argparse.ArgumentTypeError("Лимит контекста должен быть положительным целым числом.")
    return limit


def model_name(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("Название модели не должно быть пустым.")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="SITW — консольный помощник")
    parser.add_argument("--backend", choices=("test", "ollama"), default="test",
                        help="Источник ответов (по умолчанию: test)")
    parser.add_argument("--model", type=model_name, default="qwen2.5:7b",
                        help="Модель Ollama (по умолчанию: qwen2.5:7b; только для ollama)")
    parser.add_argument("--timeout", type=positive_timeout, default=120.0,
                        help="Тайм-аут операции сокета в секундах (по умолчанию: 120; только для ollama)")
    parser.add_argument("--context-messages", type=positive_context_messages, default=40,
                        help="Максимум сообщений контекста, включая текущее (по умолчанию: 40; только для ollama)")
    args = parser.parse_args(argv)
    try:
        storage = Storage()
    except (sqlite3.Error, OSError) as exc:
        print(f"SITW: Ошибка открытия хранилища: {exc}", file=sys.stderr)
        return 1

    assistant = None
    status = 0
    try:
        assistant = (
            Assistant(OllamaBackend(model=args.model, timeout=args.timeout))
            if args.backend == "ollama"
            else Assistant()
        )
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
                if args.backend == "ollama":
                    response = assistant.respond(
                        message, history=storage.get_history(limit=args.context_messages)
                    )
                else:
                    response = assistant.respond(message)
            except GenerationError as exc:
                reason = (
                    "получен пустой или некорректный ответ"
                    if isinstance(exc, InvalidResponseError)
                    else "сбой backend"
                )
                for error_type, safe_reason in (
                    (ServerUnavailableError, "не удалось подключиться к Ollama"),
                    (ModelUnavailableError, "запрошенная модель недоступна"),
                    (ResponseInterruptedError, "получение ответа прервано"),
                ):
                    if isinstance(exc, error_type):
                        reason = safe_reason
                        break
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
