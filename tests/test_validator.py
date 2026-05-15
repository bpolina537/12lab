import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from webinar.utils.validate_webinar_id import validate_webinar_id


def test_valid_with_dash():
    assert validate_webinar_id("WEB-12345") is True


def test_valid_without_dash():
    assert validate_webinar_id("WEB12345") is True


def test_valid_with_zeros():
    assert validate_webinar_id("WEB-00000") is True


def test_invalid_lowercase():
    assert validate_webinar_id("web-12345") is False


def test_invalid_4_digits():
    assert validate_webinar_id("WEB-1234") is False


def test_invalid_6_digits():
    assert validate_webinar_id("WEB-123456") is False


def test_invalid_letters():
    assert validate_webinar_id("WEB-12A45") is False


def test_invalid_no_prefix():
    assert validate_webinar_id("12345") is False


def test_invalid_empty():
    assert validate_webinar_id("") is False