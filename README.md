README.md  
Webinar Platform API
Вариант 20 — Платформа для проведения вебинаров — лабораторная работа №12

Данные для проверки

| Поле | Значение                                                                  |
|------|---------------------------------------------------------------------------|
| **ФИО** | Бондаренко Полина Кирилловна                                              |
| **Группа** | 221331                                                                    |
| **Вариант** | 20                                                                        |
| **Предметная область** | Платформа для проведения вебинаров (комнаты,записи,чат,опросы, статистика |
| **Номер лабораторной** | 12                                                                        |

 Выполненные задания средней сложности (адаптация под вариант 20)

Согласно методичке для вариантов 1–10 выполняются **10 заданий** средней сложности. 

Выполненные задания

| № | Содержание | Где находится |
|---|---|---|
| 1 | Генерация CRUD-приложения на FastAPI для вебинаров | `src/webinar/main.py` |
| 2 | Генерация pytest тестов для CRUD API | `tests/test_main.py` |
| 3 | Рефакторинг плохого кода расчёта активности | `src/webinar/activity.py` |
| 4 | Dockerfile и docker-compose | `Dockerfile`, `docker-compose.yml` |
| 5 | Объяснение сложной бизнес-логики | `docs/activity_explanation.md` |
| 6 | Генерация README документации | `README.md` |
| 7 | Alembic миграции базы данных | `migrations/` |
| 8 | Поиск уязвимостей и code review | `docs/CODE_REVIEW.md` |
| 9 | Генерация SQL аналитического запроса | `tests/test_sql_queries.py` |
| 10 | Regex для ID вебинара | `src/webinar/utils/validate_webinar_id.py` |

Дополнительно:

- использованные промты  — `PROMPT_LOG.md`

---

Стек технологий

  - FastAPI
  - Python 3.11
  - Pytest
  - PostgreSQL
  - SQLAlchemy
  - Alembic
  - Docker
  - Docker Compose

---

 Возможности проекта

  - CRUD вебинаров
  - чат вебинара
  - опросы участников
  - записи вебинаров
  - аналитика активности
  - Docker-конфигурация
  - Alembic миграции
  - автоматические тесты

---

Запуск проекта

Локальный запуск

Установка зависимостей:

    pip install -r requirements.txt 

Запуск приложения:

    uvicorn src.webinar.main:app --reload
    Docker

Сборка контейнера:

    docker build -t webinar-platform .

Запуск через Docker Compose:

    docker compose up --build 

Тестирование

Запуск тестов:

    pytest -v

Покрытие:

    pytest --cov=src

Покрытие тестами ≥ 70%.

SQL аналитический запрос

Топ-5 вебинаров по количеству сообщений за последние 7 дней:

    SELECT
        r.id AS room_id,
        r.title,
        COUNT(cm.id) AS messages_count
    FROM rooms r
    JOIN chat_messages cm
        ON r.id = cm.room_id
    WHERE cm.timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY r.id, r.title
    ORDER BY messages_count DESC
    LIMIT 5; 

Regex для ID вебинара

Поддерживаемые форматы:

    WEB-12345
    WEB12345

Регулярное выражение:
    
    r"^WEB-?\d{5}$"

Безопасность и code review

В ходе анализа были найдены проблемы:

    XSS в чате
    отсутствие аутентификации
    отсутствие rate limiting
    возможность повторного голосования
    недостаточная обработка ошибок

Отчёт с рекомендациями находится в:

    docs/CODE_REVIEW.md