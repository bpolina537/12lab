import sys
from pathlib import Path

# Добавляем src в путь импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from webinar.main import app


@pytest.fixture
def client():
    """Фикстура для тестирования API"""
    return TestClient(app)


@pytest.fixture
def sample_room():
    """Фикстура с тестовой комнатой"""
    return {
        "title": "Тестовый вебинар",
        "speaker": "Анна Смирнова",
        "start_time": "2026-05-20T15:00:00Z",
        "status": "pending"
    }


@pytest.fixture
def sample_message():
    """Фикстура с тестовым сообщением"""
    return {
        "username": "test_user",
        "message": "Привет, мир!"
    }


@pytest.fixture
def sample_poll():
    """Фикстура с тестовым опросом"""
    return {
        "question": "Как вам вебинар?",
        "options": ["Отлично", "Хорошо", "Нормально", "Плохо"]
    }