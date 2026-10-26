# SITW — Something In The Way

**An offline-first AI companion designed to support people through difficult moments.**

> Even amid all this darkness, I see the light.
>
> «Даже среди всей этой тьмы — я вижу свет».

SITW is a personal software project focused on building a free, customizable, and autonomous AI companion. Its purpose is to provide a reliable point of support when everyday life becomes difficult, helping users organize their thoughts and find their next step.

The project is inspired by the idea of a personal Batcomputer: a locally controlled assistant with memory, configurable behavior, and an extensible architecture.

**SITW is under active development.** The current repository contains an early prototype, and its architecture is being reworked toward an independent core.

## Why SITW exists

SITW began with a personal experience of burnout.

During difficult periods, even deciding what to do next can become overwhelming. Conversations with an AI assistant helped me find a point of reference and work through moments when I felt stuck.

However, relying on a browser-based service has limitations. I wanted to explore a different approach: an assistant that runs locally, preserves user-controlled context, and does not depend on a mandatory cloud service.

SITW is my attempt to turn that idea into a practical tool that may help other people, too.

AI is not a replacement for human relationships or professional support. SITW aims to be an additional tool people can turn to when they need help organizing their thoughts or finding a manageable next step.

## Current development direction

The project is moving from a Telegram-centered prototype toward an independent application core.

The first priority is to establish a reliable foundation before expanding the feature set.

Current development priorities:

- **Independent core** — business logic separated from communication interfaces.
- **CLI / CMD execution** — the core should be runnable without a graphical interface or Telegram.
- **Reliable data storage** — SQLite, safe schema migrations, and persistent application state.
- **Local AI** — integration with a locally running language model.
- **Memory and personalization** — user-controlled context and configurable assistant behavior.
- **Extensibility** — a modular architecture for future features and integrations.

Telegram is currently a prototype interface and testing environment, not the intended final form of SITW.

## Long-term vision

The planned architecture includes several independent components:

- **Core** — application logic and coordination.
- **Local AI** — local language model inference.
- **Memory** — persistent context and user settings.
- **Workshop** — extensible local configuration and feature packages.
- **RPG** — optional quests and learning systems.
- **User Interface** — a standalone application with customizable appearance.
- **Audio** — optional voice interaction and sound features.
- **Safety** — safeguards, predictable behavior, and transparent limitations.

These are development goals, not a claim that every component is already implemented.

RPG features are optional and separate from the assistant's primary purpose. SITW should support users rather than turn recovery into another productivity system.

## Core principles

### Free for everyone

SITW is intended to remain free. There will be no paid subscriptions, paid features, or functionality locked behind payments.

Before a formal partnership, voluntary user donations are the project's only planned source of income. Donations will not unlock features or provide advantages.

### Offline-first

The long-term goal is for core functionality to operate locally without requiring an internet connection or a paid cloud API.

This capability is still under development and must be verified through testing.

### User-controlled data

Memory and application state should remain under the user's control. Data integrity, backups, safe migrations, and transparent limitations are important design requirements.

### Personalization

Users should be able to configure the assistant's communication style and appearance. Customization is part of the intended experience, not a reward for progression or payment.

### Reliability over feature count

The project prioritizes a stable core, explicit module boundaries, tests, and recoverable data over rapid feature expansion.

### Responsible support

SITW should not shame users for inactivity, manipulate emotional attachment, or claim to replace professional care. It must be honest about its capabilities and limitations.
### Honest project status

SITW distinguishes implemented features, tested capabilities, prototypes, and planned functionality. Documentation must not present an architectural goal as a delivered feature or claim reliability without supporting tests.

## Collaboration

SITW is an independent project, but its long-term vision may require a team.

I am open to collaboration with developers, researchers, and companies working on local AI, privacy-focused software, personalization, and human-centered AI products.

I am particularly interested in opportunities to contribute to a team that could help develop SITW into a reliable, accessible product.

The goal of collaboration is to expand what the project can achieve while preserving its core principles: accessibility, user control, and support without financial barriers.

## Project status

SITW is currently in an early development stage.

The immediate objective is to stabilize the existing prototype, separate the application core from Telegram-specific logic, and establish a testable foundation for local AI integration.

The roadmap may change as implementation and testing reveal new requirements. Planned features should not be interpreted as completed functionality.

Contributions, technical feedback, and thoughtful collaboration are welcome.

---

**SITW — Something In The Way**

*Even amid all this darkness, I see the light.*

## Текущий статус

**Pre-alpha / разработка ядра.**

Текущий этап — проверка базовой логики через Telegram-прототип. Отдельное настольное приложение и полноценная локальная языковая модель остаются следующими этапами разработки.

В проекте планируются:
- локальное хранение данных на SQLite;
- автономный инференс языковой модели;
- настраиваемое поведение и расширения Workshop;
- RPG-система и отдельная система обучения;
- самостоятельное приложение с настраиваемым интерфейсом.

Не все перечисленные возможности реализованы. Статус компонентов и результаты тестирования будут документироваться по мере разработки.

---

## 🪵 Дневник Разработчика (DevLog)

### [Патч v2.1 - v2.2 Alpha] — Инициализация Реактора (24.10.2026)
* **Статус Лидера:** Ментальная батарейка после 8-часовой смены у плавильных печей — 10%. Внутренний критик уничтожен сухими фактами рынка.
* **Технические победы за сегодня:**
  1. Развернут локальный Dev-контур (Python 3.15 + VS Code).
  2. Физически материализовано ядро базы данных `sitw_cave.db`.
  3. Создана первая умная таблица `users` с контуром кастомного имени напарника.
  4. Успешно запущен первый в истории Organic Onboarding. Данные Лидера (Брюс) и Напарника (Альфред) запечатаны в локальную сталь. Проведена первичная проверка структуры базы данных через DB Browser. Полноценная проверка корректности логирования требует дополнительных тестов.
### [Патч v2.3 Alpha] — Архитектура Квестов и Первые Трофеи (24.10.2026)
* Развернута новая таблица `quests` для управления Сюжетками и Дейликами.
* База данных научилась понимать типы задач (Daily/Main/Rescue) и баланс начисления EXP.
* Накатан скрипт `update_v23.py`. Все выполненные за сегодня квесты занесены в локальный журнал.
### [Патч v2.3 - v2.4 Alpha] — Движок расчета EXP и Выход на 2 LVL (24.10.2026)
* Успешно спроектирована и внедрена таблица `quests` для разделения задач на Daily/Main/Rescue.
* Набран и запущен математический процессор ядра `engine_v24.py`.
* База данных научилась автоматически сканировать выполненные квесты, суммировать опыт и управлять прогрессом Лидера.
* Профиль пользователя "Брюс" успешно перешагнул отметку в 100 EXP и зафиксировал переход на **2-й Уровень (LVL 2)**. Логи стерильны.
### [Патч v2.5 Alpha] — Автоматический Quest Resolver и Сквозной Вызов (24.10.2026)
* Спроектирован и запущен движок закрытия контрактов `resolve_v25.py`.
* Реализован протокол бесшовного сквозного вызова (`subprocess`): скрипт закрытия квестов сам пингует математическое ядро `engine_v24.py` для мгновенного перерасчета EXP и уровня.
* Локальная архитектура полностью автономна, логи стерильны и проверены. Спринт закрыт на абсолютном максимуме производительности.
### [Патч v2.6 Alpha] — Тотальное закрытие Локального Контура Базы (24.10.2026)
* Спроектированы и развернуты финальные таблицы `mental_logs` (Менталка) и `chat_logs` (Болталка).
* База данных полностью готова к умному анализу хаотичной речи без анкет и интерфейсной усталости.
* Проведена тестовая запись реального ночного выгорания Лидера (10% заряда аккумулятора). Данные сохранены локально.
* Фундамент `sitw_cave.db` подготовлена начальная схема БД и предстоит проверка совместимости, сохранения состояния и восстановления после перезапуска. 
### [Патч v3.0 Alpha] — Сетевая Инициализация и Регистрация Бота (24.10.2026)
* Официально зарегистрирован бот в Telegram экосистеме под управлением Узла 8.
* Развернута сетевая библиотека `pyTelegramBotAPI` в локальном Dev-контуре.
* Накатан сетевой каркас `bot_v30.py`. Тестовый пинг серверов прошел успешно. Связь установлена.
### [Патч v3.0 Alpha] — Инициализация Сетевого Реактора Telegram (24.10.2026)
* **Продуктовая цель:** Полное уничтожение интерфейсной усталости (UI Fatigue) и лагов браузера. Перенос структуры ИИ-штурмана Альфреда напрямую в мессенджер Telegram.
* **Результат:** Развернута сетевая библиотека `pyTelegramBotAPI` в локальном Dev-контуре. Накатан сетевой каркас `bot_v30.py` со сквозным роутингом: ключевые слова (`Лог`, `Менталка`) автоматически триггерят запись в SQLite-таблицу `mental_logs`, а обычный текст улетает в `chat_logs`. Интегрирован жесткий периметр безопасности с фильтрацией по уникальному `BRUCE_ID` из скрытого локального `config.py`.

---

### [Патчи v3.0.1 - v3.0.5] — Калибровка ИИ-Ядра и Эволюция Сверхвыживаемости Сети
> *Серия минорных архитектурных патчей для тонкой настройки и калибровки ИИ-функции перехвата сообщений.*

* **v3.0.1 — Защита от Ошибки 400 & Google API Geo-Block:**
  Инициализирован контур `google-genai` с зашитым Психологическим ДНК Альфреда (`ALFRED_PROMPT`). В ходе тестов столкнулись с жесткой региональной блокировкой Google API для СНГ-региона. Сетевые рельсы оперативно перестроены на OpenAI SDK через прокси-агрегатор `gpt-4o-mini` для обхода блокировок напрямую без VPN.

* **v3.0.2 — Фильтрация Длины строк & HTML-Leaks:**
  Выявлен инфраструктурный баг провайдера: при пиковых вечерних нагрузках шлюз ProxyAPI падал и вместо JSON выплескивал сырой HTML-код своей страницы авторизации, вызывая в `telebot` ошибку `400 Bad Request: text is too long`. Внедрен жесткий фильтр длины текста на уровне Python (`ai_reply[:1000]`), предназначенный для предотвращения ошибки отправки слишком длинного сообщения в Telegram.

* **v3.0.3 — Перевод на GitHub Models & Адаптивный Парсинг:**
  Выполнен переход на официальный бесплатный шлюз ИИ-вычислений `[GitHub Models](https://github.com/marketplace/models)` под учетной записью `BatmanFromSarov`. Столкнулись с задержкой активации Fine-grained токена на серверах Microsoft Azure и ошибкой совместимости типов (`'str' object has no attribute 'choices'`). Написан отказоустойчивый двухвариантный парсер типов данных на чистом Python (`isinstance(response, str)`).

* **v3.0.4 — Внедрение Локальной Матрицы Выживания (Failover Контур):**
  Реализован отказоустойчивый контур автоматического резервирования (Failover) из нескольких распределенных сетевых шлюзов. Развернут **Локальный Эмулятор ИИ Альфреда** на базе случайных кинематографичных текстовых пресетов (`random.choice`). При полном обрыве внешней сети бот не падает, а выдает кастомный нуарный ответ, идеально попадающий в контекст Бэтпещеры, и намертво запечатывает логи в SQLite-таблицу `chat_logs`.

###### SITW Devlog — переход к независимому ядру

**Статус:** архитектура пересматривается.

По мере развития SITW стало понятно, что дальнейшее добавление функций в Telegram-прототип без чёткого разделения бизнес-логики и интерфейса усложнит развитие проекта.

Поэтому я меняю приоритет разработки.

Вместо того чтобы продолжать наращивать функциональность бота, я сосредоточусь на независимом ядре SITW, которое сможет запускаться через CMD без Telegram и графического интерфейса.

Это позволит сначала проверить основные механизмы системы, надёжность хранения данных и взаимодействие компонентов, а затем подключать разные интерфейсы к одному ядру.

**Новый порядок работы:**
1. Проверка и стабилизация существующего прототипа.
2. Выделение независимого ядра.
3. Надёжная работа с SQLite и состоянием приложения.
4. Подготовка архитектуры к подключению локальной языковой модели.
5. Постепенное возвращение и расширение пользовательских функций.

Telegram остаётся частью истории и тестирования SITW, но больше не определяет архитектуру всего проекта.

Цель не изменилась: создать бесплатного, настраиваемого и автономного ИИ-помощника, который сможет стать точкой опоры для человека в трудный момент.

Изменился путь реализации — теперь приоритетом становится надёжный фундамент.

