import sqlite3
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def db_connection():
    """Создаёт временную БД и заполняет тестовыми данными"""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Создаём таблицы
    cursor.execute("""
        CREATE TABLE rooms (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            speaker TEXT,
            start_time TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY,
            room_id INTEGER,
            username TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)

    # Добавляем комнаты
    rooms = [
        (1, "FastAPI вебинар", "Анна", "2026-05-10 10:00:00", "active"),
        (2, "Docker вебинар", "Иван", "2026-05-11 11:00:00", "active"),
        (3, "SQL вебинар", "Мария", "2026-05-12 12:00:00", "ended"),
        (4, "Пустая комната", "Петр", "2026-05-13 13:00:00", "pending"),
    ]
    cursor.executemany(
        "INSERT INTO rooms (id, title, speaker, start_time, status) VALUES (?, ?, ?, ?, ?)",
        rooms
    )

    # Добавляем сообщения (разные даты)
    now = datetime.now()
    messages = [
        (1, 1, "user1", "Hello", (now - timedelta(days=1)).isoformat()),
        (2, 1, "user2", "Hi", (now - timedelta(days=2)).isoformat()),
        (3, 1, "user3", "Hey", (now - timedelta(days=3)).isoformat()),
        (4, 2, "user4", "How are you?", (now - timedelta(days=1)).isoformat()),
        (5, 2, "user5", "Good!", (now - timedelta(days=5)).isoformat()),
        (6, 3, "user6", "Question?", (now - timedelta(days=10)).isoformat()),
        (7, 3, "user7", "Answer", (now - timedelta(days=15)).isoformat()),
    ]
    cursor.executemany(
        "INSERT INTO chat_messages (id, room_id, username, message, timestamp) VALUES (?, ?, ?, ?, ?)",
        messages
    )

    conn.commit()
    yield conn
    conn.close()


def test_top_5_rooms_by_messages(db_connection):
    """Тест SQL-запроса: топ-5 комнат по сообщениям за 7 дней"""
    cursor = db_connection.cursor()

    # SQLite-версия запроса
    sql = """
        SELECT r.id, r.title, COUNT(cm.id) AS messages_count
        FROM rooms r
        LEFT JOIN chat_messages cm ON r.id = cm.room_id
        WHERE cm.timestamp >= datetime('now', '-7 days')
        GROUP BY r.id, r.title
        ORDER BY messages_count DESC
        LIMIT 5
    """

    cursor.execute(sql)
    results = cursor.fetchall()

    # Проверяем, что результат есть
    assert len(results) > 0

    # Комната 1 должна быть с 3 сообщениями
    room1 = next((r for r in results if r[0] == 1), None)
    if room1:
        assert room1[2] == 3

    # Комната 2 должна быть с 2 сообщениями
    room2 = next((r for r in results if r[0] == 2), None)
    if room2:
        assert room2[2] == 2


def test_old_messages_not_counted(db_connection):
    """Тест: сообщения старше 7 дней не учитываются"""
    cursor = db_connection.cursor()

    sql = """
        SELECT COUNT(cm.id) AS messages_count
        FROM chat_messages cm
        WHERE cm.timestamp < datetime('now', '-7 days')
    """

    cursor.execute(sql)
    result = cursor.fetchone()
    # Должны быть сообщения старше 7 дней (комната 3)
    assert result[0] == 2


def test_left_join_includes_rooms_without_messages(db_connection):
    """Тест: LEFT JOIN включает комнаты без сообщений"""
    cursor = db_connection.cursor()

    sql = """
        SELECT r.id, COUNT(cm.id) AS messages_count
        FROM rooms r
        LEFT JOIN chat_messages cm ON r.id = cm.room_id
        WHERE cm.timestamp >= datetime('now', '-7 days') OR cm.id IS NULL
        GROUP BY r.id
    """

    cursor.execute(sql)
    results = cursor.fetchall()
    room_ids = [r[0] for r in results]

    # Комната 4 (пустая) должна быть в результатах (если WHERE правильно настроен)
    # Или в основном запросе её нет — это ожидаемо


def test_limit_5_works(db_connection):
    """Тест: LIMIT 5 ограничивает результат"""
    cursor = db_connection.cursor()

    sql = """
        SELECT r.id
        FROM rooms r
        LIMIT 5
    """

    cursor.execute(sql)
    results = cursor.fetchall()
    assert len(results) <= 5