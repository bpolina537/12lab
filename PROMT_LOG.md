# Вариант 20 — Платформа для проведения вебинаров

Ниже приведены промпты, использованные при разработке проекта.  
Промпты расположены в порядке работы с субагентами:

- Claude Code — backend, FastAPI, тесты, Docker, миграции, рефакторинг
- Grok — документация, аналитика, SQL, безопасность, regex, README

---

CLAUDE CODE

Задание 1

1. FastAPI REST API для платформы вебинаров

Ты — senior Python разработчик. 
Напиши REST API на FastAPI для платформы вебинаров.

Модели данных

Room (комната/вебинар)

- id (int, автоинкремент)
- title (str, название вебинара)
- speaker (str, имя спикера)
- start_time (datetime)
- status (str: pending/active/ended)
- created_at (datetime)

Recording (запись)

- id (int)
- room_id (int, внешний ключ к Room)
- video_url (str)
- duration (int, секунды)
- recorded_at (datetime)

 ChatMessage (сообщение чата)

- id (int)
- room_id (int)
- username (str)
- message (str)
- timestamp (datetime)

Poll (опрос)

- id (int)
- room_id (int)
- question (str)
- options (list[str], варианты ответов)

PollAnswer (ответ на опрос)

- id (int)
- poll_id (int)
- room_id (int)
- username (str)
- selected_option (str)

Эндпоинты

- CRUD для комнат
- POST /rooms/{id}/chat
- GET /rooms/{id}/chat
- POST /rooms/{id}/polls
- POST /polls/{id}/answer
- GET /rooms/{id}/statistics
- POST /rooms/{id}/recordings
- GET /rooms/{id}/recordings

Требования

- Валидация через Pydantic
- Обработка ошибок (404, 400)
- Type hints
- Хранение in-memory (списки/словари)
- Один файл `main.py`

---

2. Добавление корневого эндпоинта "/"

У меня есть FastAPI приложение для платформы вебинаров (`main.py`), которое ты написал.

При запуске:

```bash
uvicorn main:app --reload
```

и открытии:

```text
http://localhost:8000
```

возникает ошибка:

```text
404 Not Found
```

Добавь GET "/" с ответом:

```json
{
  "message": "Webinar Platform API is running",
  "docs": "/docs"
}
```

Не изменяй существующие эндпоинты — только добавь корневой.

---

Задание 2

3. Pytest тесты для FastAPI приложения

Ты — senior Python тестировщик.

Напиши модульные тесты pytest для FastAPI приложения платформы вебинаров.

Покрой:

- создание комнаты
- получение комнаты по ID
- обновление и удаление комнаты
- отправка сообщения в чат
- получение сообщений чата
- создание опроса и ответ на опрос
- получение статистики комнаты
- создание и получение записей

Граничные случаи

- пустой текст сообщения
- несуществующая комната
- невалидные статусы

Требования

- Используй TestClient от FastAPI
- Покрытие не менее 70%
- Дай файл `test_main.py`

---

4. Исправление datetime.utcnow()

В файле `main.py` есть предупреждения `DeprecationWarning` из-за `datetime.utcnow()`.

### Выполни

- Замени ВСЕ `datetime.utcnow()` на `datetime.now(timezone.utc)`
- Импорт:

```python
from datetime import datetime, timezone
```

- Удали дублирующиеся импорты datetime
- Не меняй больше ничего
- После исправления pytest должен проходить без предупреждений

Коммит

```bash
git commit -m "fix: replace deprecated datetime.utcnow() with timezone-aware datetime in main.py"
```

---

Задание 3

5. Рефакторинг плохого кода (activity.py)

Ты — senior Python разработчик.

Выполни рефакторинг функции расчёта активности участника вебинара.

 Проблемы

- магические числа
- дублирование логики
- нет type hints
- функция делает слишком много
- глубокая вложенность
- мутация входных данных
- нет обработки ошибок
- плохие имена переменных

Требования

- разбей на 3-4 функции
- добавь type hints
- вынеси константы
- убери глобальный кэш
- обработка ошибок
- docstrings
- максимум 2 уровня вложенности
- валидация входных данных

---

Задание 4

6. Docker + Docker Compose

Ты — DevOps инженер. Для FastAPI приложения платформы вебинаров создай Dockerfile и docker-compose.yml.

Dockerfile: образ Python 3.11, установка зависимостей (fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary), копирование кода, команда запуска через uvicorn.

docker-compose.yml: сервис app (сборка из Dockerfile, порт 8000:8000), сервис db (postgres:15), сервис для миграций Alembic (запускается перед app). 
Добавь healthcheck для БД, переменные окружения из .env. Дай два файла.

---

GROK

Задание 5

8. Объяснение calculate_engagement_score

Ты — технический писатель. Объясни простым языком, как работает следующий код (функция расчёта вовлечённости участников вебинара). 
Используй аналогию с реальной жизнью. 
Предложи 2-3 улучшения по читаемости или производительности.


Нужно

- Аналогия из реальной жизни
- Разбор факторов:
  - сообщения
  - опросы
  - время просмотра
- Бонус и штраф
- 2 проблемы кода
- 2 улучшения

Формат

- Markdown
- таблицы
- заголовки
- объяснение для новичка

---

Задание 6

9. README.md для платформы вебинаров

Ты — технический писатель. Создай полную документацию README.md для платформы вебинаров на FastAPI. Включи:

название и описание проекта

требования (Python 3.11+, Docker опционально)

инструкцию по установке и запуску (локально: pip install, uvicorn; через Docker: docker-compose up)

описание API эндпоинтов с примерами запросов и ответов (комнаты, чат, опросы, записи, статистика)

переменные окружения (DATABASE_URL, SECRET_KEY)

примеры curl-запросов

Дай готовый README.md.
---

Задание 7

10. Alembic миграции

Ты — backend разработчик. Создай SQL миграции для Alembic для платформы вебинаров. Таблицы:

rooms (id, title, speaker, start_time, status, created_at)

recordings (id, room_id → rooms.id, video_url, duration, recorded_at)

chat_messages (id, room_id → rooms.id, username, message, timestamp)

polls (id, room_id → rooms.id, question, options_json)

poll_answers (id, poll_id → polls.id, room_id, username, selected_option)

Добавь индексы: created_at в rooms, timestamp в chat_messages, room_id во всех связанных таблицах. 
Учти ON DELETE CASCADE для записей/сообщений/опросов при удалении комнаты. 
Дай код миграции в migration.py.
---

11. Исправление SQLite JSONB ошибки

У меня ошибка:

```text
Compiler can't render element of type JSONB
```

SQLite не поддерживает JSONB.

Замени JSONB на

```python
sa.JSON()
```

Дай полный исправленный файл миграции.

---

12. Проверка существования таблиц в Alembic

Ошибка:

```text
table rooms already exists
```

Добавь проверки:

```python
if not bind.dialect.has_table(bind, "rooms"):
```

для всех таблиц.

---

Задание 8

13. Security audit

Ты — security expert. Проведи аудит безопасности кода платформы вебинаров. Ищи:

XSS в сообщениях чата (если не экранируется текст)

отсутствие аутентификации (кто угодно пишет в чат от любого имени)

SQL-инъекции (если используется сырой SQL)

незащищённые эндпоинты (доступ к записям без проверки)

отсутствие rate limiting (флуд в чате)

валидация опросов (можно ли проголосовать несколько раз)

Напиши отчёт в формате «Проблема → Риск → Рекомендация». Дай 5+ проблем.

---

Задание 9

14. SQL аналитический запрос

Ты — аналитик данных. Напиши SQL-запрос для платформы вебинаров: «Топ-5 комнат по количеству сообщений в чате за последние 7 дней».
Выведи: room_id, title, messages_count. 
Отсортируй по messages_count DESC, ограничь 5. Объясни логику запроса: какие JOIN, GROUP BY, WHERE и зачем. Дай запрос и объяснение.

Вывести

- room_id
- title
- messages_count

Добавь объяснение

- JOIN
- GROUP BY
- WHERE
- ORDER BY
- LIMIT

---

Задание 10

15. Regex для ID вебинара

Ты — разработчик. 
Напиши регулярное выражение для валидации ID вебинара в платформе. 
Формат: «WEB-» + 5 цифр, например WEB-12345. 
Также может быть короткая версия: «WEB» + 5 цифр, например WEB12345. 
Невалидные примеры: web-12345 (строчные), WEB-1234 (4 цифры), WEB-123456 (6 цифр), WEB-12A45 (буквы). 
Напиши скрипт на Python, который проверяет список примеров (5 валидных, 5 невалидных) и выводит PASS/FAIL. Используй модуль re. Дай regex и скрипт.

---

Юнит-тесты

 16. Полный комплект pytest тестов

Ты — senior Python тестировщик.

Напиши:

- tests/test_crud.py
- tests/test_activity.py
- tests/test_migrations.py
- tests/test_sql_queries.py
- tests/test_validator.py
- tests/conftest.py

Используй

- pytest
- TestClient
- SQLite in-memory
- фикстуры
- покрытие ≥70%
