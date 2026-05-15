import re

# Регулярное выражение
WEBINAR_ID_PATTERN = re.compile(r'^WEB-?\d{5}$')


def validate_webinar_id(webinar_id: str) -> bool:
    """Проверяет, соответствует ли ID формату вебинара"""
    return bool(WEBINAR_ID_PATTERN.match(webinar_id))


# ==================== ТЕСТЫ ====================

test_cases = [
    # Валидные примеры
    ("WEB-12345", True),
    ("WEB12345", True),
    ("WEB-98765", True),
    ("WEB00000", True),
    ("WEB-11111", True),

    # Невалидные примеры
    ("web-12345", False),  # строчные буквы
    ("WEB-1234", False),  # 4 цифры
    ("WEB-123456", False),  # 6 цифр
    ("WEB-12A45", False),  # буква внутри
    ("WEB-123", False),  # 3 цифры
    ("12345", False),  # без префикса
    ("WEB1234", False),  # 4 цифры без дефиса
]

print("=== Тестирование валидации ID вебинара ===\n")

for webinar_id, expected in test_cases:
    result = validate_webinar_id(webinar_id)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status} | {webinar_id:15} → {'Valid' if result else 'Invalid'}")