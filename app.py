from sitw.core.assistant import Assistant


def main():
    assistant = Assistant()

    print("SITW — Something In The Way")
    print("Для выхода введи: exit")

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

        response = assistant.respond(message)
        print(f"SITW: {response}")


if __name__ == "__main__":
    main()