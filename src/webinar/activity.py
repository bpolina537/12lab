# activity.py
from datetime import datetime, timezone
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Message scoring thresholds
MSG_REACTIONS_TIER1 = 5
MSG_REACTIONS_TIER2 = 10
MSG_LENGTH_TIER1 = 100
MSG_LENGTH_TIER2 = 500

MSG_SCORE_BASE = 1
MSG_SCORE_REACTIONS_TIER1 = 2
MSG_SCORE_REACTIONS_TIER2 = 3
MSG_LENGTH_MULTIPLIER_TIER1 = 1.5
MSG_LENGTH_MULTIPLIER_TIER2 = 2.0

# Poll scoring thresholds
POLL_ANSWERS_DIVISOR = 10
POLL_SCORE_MAX_BASE = 5
POLL_VOTERS_TIER1 = 20
POLL_VOTERS_TIER2 = 50
POLL_BONUS_TIER1 = 3
POLL_BONUS_TIER2 = 5

# Mode multipliers
MODE_MULTIPLIERS: dict[str, dict[str, float]] = {
    "strict": {"msg": 0.8, "poll": 0.9},
    "boost":  {"msg": 1.2, "poll": 1.1},
    "normal": {"msg": 1.0, "poll": 1.0},
}

# Participation bonus thresholds
BONUS_TIERS: list[tuple[int, int]] = [
    (100, 50),
    (50,  25),
    (20,  10),
]

VALID_ITEM_TYPES = {"msg", "poll"}
VALID_MODES = set(MODE_MULTIPLIERS.keys())


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RoomStats:
    room_id: str
    total: float
    avg: float
    count: int
    bonus: int
    final: float
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _score_message(item: dict, mode: str) -> float:
    """Calculate the activity score for a single chat message.

    Args:
        item: Dict with keys 'reactions' (int) and 'text' (str).
        mode: Scoring mode — 'strict', 'boost', or 'normal'.

    Returns:
        Float score for this message.
    """
    reactions = item.get("reactions", 0)
    text_len = len(item.get("text", ""))

    if reactions > MSG_REACTIONS_TIER2:
        score = MSG_SCORE_REACTIONS_TIER2
    elif reactions > MSG_REACTIONS_TIER1:
        score = MSG_SCORE_REACTIONS_TIER1
    else:
        score = MSG_SCORE_BASE

    if text_len > MSG_LENGTH_TIER2:
        score *= MSG_LENGTH_MULTIPLIER_TIER2
    elif text_len > MSG_LENGTH_TIER1:
        score *= MSG_LENGTH_MULTIPLIER_TIER1

    return score * MODE_MULTIPLIERS[mode]["msg"]


def _score_poll(item: dict, mode: str) -> float:
    """Calculate the activity score for a single poll.

    Args:
        item: Dict with keys 'answers' (int) and 'unique_voters' (int).
        mode: Scoring mode — 'strict', 'boost', or 'normal'.

    Returns:
        Float score for this poll.
    """
    answers = item.get("answers", 0)
    if answers <= 0:
        return 0.0

    base = min(answers / POLL_ANSWERS_DIVISOR, 1.0) * POLL_SCORE_MAX_BASE

    unique_voters = item.get("unique_voters", 0)
    voter_bonus = 0
    if unique_voters > POLL_VOTERS_TIER2:
        voter_bonus = POLL_BONUS_TIER1 + POLL_BONUS_TIER2
    elif unique_voters > POLL_VOTERS_TIER1:
        voter_bonus = POLL_BONUS_TIER1

    return (base + voter_bonus) * MODE_MULTIPLIERS[mode]["poll"]


def _participation_bonus(count: int) -> int:
    """Return a flat bonus based on total item count.

    Args:
        count: Total number of scored items.

    Returns:
        Integer bonus points.
    """
    for threshold, bonus in BONUS_TIERS:
        if count > threshold:
            return bonus
    return 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_items(items: list[dict], mode: str) -> tuple[list[dict], float]:
    """Score each item in the list and return annotated copies plus total.

    Items are never mutated; each result dict is a shallow copy with 'score' added.

    Args:
        items: List of activity item dicts. Each must contain a 'type' key
               with value 'msg' or 'poll'.
        mode:  Scoring mode — 'strict', 'boost', or 'normal'.

    Returns:
        Tuple of (scored_items, total_score).

    Raises:
        ValueError: If mode is not recognised or any item is missing 'type'.
        TypeError:  If items is not a list.
    """
    if not isinstance(items, list):
        raise TypeError(f"items must be a list, got {type(items).__name__}")
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}, got {mode!r}")

    scored: list[dict] = []
    total = 0.0

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"Item at index {idx} is not a dict")
        item_type = item.get("type")
        if item_type not in VALID_ITEM_TYPES:
            raise ValueError(
                f"Item at index {idx} has invalid type {item_type!r}; "
                f"expected one of {VALID_ITEM_TYPES}"
            )

        score = _score_message(item, mode) if item_type == "msg" else _score_poll(item, mode)
        scored.append({**item, "score": score})
        total += score

    return scored, total


def compute_room_stats(
    items: list[dict],
    room_id: str,
    mode: str = "normal",
    cache: dict | None = None,
) -> RoomStats:
    """Compute activity statistics for a webinar room.

    Args:
        items:   List of activity items (dicts with at least a 'type' key).
        room_id: Identifier for the room; used as cache key if cache provided.
        mode:    Scoring mode — 'strict', 'boost', or 'normal'. Defaults to 'normal'.
        cache:   Optional dict to store computed stats. Mutated in-place if provided.

    Returns:
        RoomStats dataclass with total, avg, count, bonus, and final scores.

    Raises:
        ValueError: If items is empty, mode is invalid, or items contain bad data.
        TypeError:  If items is not a list.
    """
    if not items:
        raise ValueError("items must not be empty")

    scored_items, total = score_items(items, mode)

    count = len(scored_items)
    avg = total / count
    bonus = _participation_bonus(count)

    stats = RoomStats(
        room_id=room_id,
        total=total,
        avg=avg,
        count=count,
        bonus=bonus,
        final=total + bonus,
    )

    if cache is not None:
        cache[room_id] = stats

    return stats


def format_report(stats: RoomStats) -> str:
    """Render a human-readable summary of room activity statistics.

    Args:
        stats: A RoomStats dataclass instance.

    Returns:
        Multi-line string report.
    """
    return (
        f"=== Room {stats.room_id} ===\n"
        f"Items:   {stats.count}\n"
        f"Total:   {stats.total:.2f}\n"
        f"Average: {stats.avg:.2f}\n"
        f"Bonus:   {stats.bonus}\n"
        f"Final:   {stats.final:.2f}\n"
    )
