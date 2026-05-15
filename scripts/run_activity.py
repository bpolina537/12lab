# run_activity.py
from src.webinar.activity import score_items, compute_room_stats, format_report

# Пример данных: сообщения и опросы
sample_items = [
    {"type": "msg", "reactions": 3, "text": "Hello world"},
    {"type": "msg", "reactions": 12, "text": "This is a very long message that exceeds one hundred characters for sure"},
    {"type": "poll", "answers": 25, "unique_voters": 30},
    {"type": "msg", "reactions": 1, "text": "Short"},
]

# 1. Посчитать score для каждого элемента
scored, total = score_items(sample_items, mode="normal")
print("=== Scored items ===")
for item in scored:
    print(f"  {item}")

print(f"\nTotal score: {total:.2f}")

# 2. Посчитать статистику по комнате
stats = compute_room_stats(sample_items, room_id="room_123", mode="boost")
print("\n" + format_report(stats))