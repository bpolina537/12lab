import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from webinar.activity import score_items, compute_room_stats, format_report, RoomStats


class TestScoreItems:
    def test_score_messages_basic(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}]
        scored, total = score_items(items, "normal")
        assert len(scored) == 1
        assert scored[0]["score"] == 1.0
        assert total == 1.0

    def test_score_messages_with_reactions(self):
        items = [{"type": "msg", "reactions": 7, "text": "Hi"}]
        scored, total = score_items(items, "normal")
        assert scored[0]["score"] == 2.0

    def test_score_messages_long_text(self):
        items = [{"type": "msg", "reactions": 0, "text": "x" * 150}]
        scored, total = score_items(items, "normal")
        assert scored[0]["score"] == 1.5

    def test_score_messages_mode_strict(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}]
        scored, total = score_items(items, "strict")
        assert scored[0]["score"] == 0.8

    def test_score_messages_mode_boost(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}]
        scored, total = score_items(items, "boost")
        assert scored[0]["score"] == 1.2

    def test_score_poll_basic(self):
        items = [{"type": "poll", "answers": 5, "unique_voters": 5}]
        scored, total = score_items(items, "normal")
        assert scored[0]["score"] == 2.5

    def test_score_poll_with_voter_bonus(self):
        items = [{"type": "poll", "answers": 10, "unique_voters": 30}]
        scored, total = score_items(items, "normal")
        assert scored[0]["score"] >= 5.0

    def test_score_poll_no_answers(self):
        items = [{"type": "poll", "answers": 0, "unique_voters": 0}]
        scored, total = score_items(items, "normal")
        assert scored[0]["score"] == 0.0

    def test_mixed_items(self):
        items = [
            {"type": "msg", "reactions": 0, "text": "Hi"},
            {"type": "poll", "answers": 10, "unique_voters": 10}
        ]
        scored, total = score_items(items, "normal")
        assert len(scored) == 2
        assert total > 0

    def test_invalid_mode(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}]
        with pytest.raises(ValueError):
            score_items(items, "invalid_mode")

    def test_invalid_item_type(self):
        items = [{"type": "unknown"}]
        with pytest.raises(ValueError):
            score_items(items, "normal")

    def test_items_not_list(self):
        with pytest.raises(TypeError):
            score_items("not a list", "normal")

    def test_item_not_dict(self):
        items = ["not a dict"]
        with pytest.raises(TypeError):
            score_items(items, "normal")


class TestComputeRoomStats:
    def test_compute_stats_basic(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}]
        stats = compute_room_stats(items, "room_123", "normal")
        assert isinstance(stats, RoomStats)
        assert stats.room_id == "room_123"
        assert stats.count == 1
        assert stats.total == 1.0
        assert stats.avg == 1.0

    def test_compute_stats_with_bonus(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}] * 30
        stats = compute_room_stats(items, "room_123", "normal")
        assert stats.bonus == 10  # >20 items = +10 bonus

    def test_empty_items_raises_error(self):
        with pytest.raises(ValueError):
            compute_room_stats([], "room_123")

    def test_cache_works(self):
        items = [{"type": "msg", "reactions": 0, "text": "Hi"}]
        cache = {}
        stats = compute_room_stats(items, "room_123", "normal", cache=cache)
        assert cache["room_123"] == stats


class TestFormatReport:
    def test_format_report(self):
        stats = RoomStats(
            room_id="room_123",
            total=10.5,
            avg=2.1,
            count=5,
            bonus=10,
            final=20.5
        )
        report = format_report(stats)
        assert "=== Room room_123 ===" in report
        assert "Items:   5" in report
        assert "Total:   10.50" in report
        assert "Average: 2.10" in report
        assert "Bonus:   10" in report
        assert "Final:   20.50" in report