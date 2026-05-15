SQL-запрос: Топ-5 самых активных комнат по количеству сообщений

Задача:
Вывести топ-5 комнат по количеству сообщений в чате **за последние 7 дней**.

Результат запроса
- `room_id`
- `title`
- `messages_count`

---

QL-запрос (PostgreSQL)

        ```sql
        SELECT 
            r.id AS room_id,
            r.title,
            COUNT(cm.id) AS messages_count
        FROM 
            rooms r
        LEFT JOIN 
            chat_messages cm ON r.id = cm.room_id
        WHERE 
            cm.timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY 
            r.id, r.title
        ORDER BY 
            messages_count DESC
        LIMIT 5;

Объяснение логики запроса

| Часть запроса | Описание | Зачем используется |
|---------------|----------|-------------------|
| `FROM rooms r` | Основная таблица — комнаты | Получаем список всех комнат |
| `LEFT JOIN chat_messages cm` | Присоединяем таблицу сообщений | Чтобы посчитать сообщения для каждой комнаты |
| `ON r.id = cm.room_id` | Условие связи таблиц | Связываем по внешнему ключу |
| `WHERE cm.timestamp >= NOW() - INTERVAL '7 days'` | Фильтрация по дате | Оставляем только сообщения за последние 7 дней |
| `COUNT(cm.id) AS messages_count` | Подсчёт количества сообщений | Основная метрика |
| `GROUP BY r.id, r.title` | Группировка по комнатам | Обязательно при использовании агрегатной функции COUNT |
| `ORDER BY messages_count DESC` | Сортировка по убыванию | Топ — самые активные комнаты сверху |
| `LIMIT 5` | Ограничение результата | Только топ-5 |

Альтернативный вариант (только активные комнаты)
Если нужно показать только комнаты, где были сообщения за последние 7 дней, используйте INNER JOIN:

        SELECT 
            r.id AS room_id,
            r.title,
            COUNT(*) AS messages_count
        FROM 
            rooms r
        INNER JOIN 
            chat_messages cm ON r.id = cm.room_id
        WHERE 
            cm.timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY 
            r.id, r.title
        ORDER BY 
            messages_count DESC
        LIMIT 5;

Примечание:

Запрос использует LEFT JOIN, чтобы учитывать комнаты даже с небольшим количеством сообщений.
Для SQLite потребуется изменить условие даты на datetime('now', '-7 days').