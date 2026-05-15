"""
pytest test suite for the Webinar Platform API (main.py).

Run:
    pip install fastapi uvicorn pytest httpx
    pytest test_main.py -v --tb=short
Coverage check:
    pip install pytest-cov
    pytest test_main.py --cov=main --cov-report=term-missing
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Import app AND in-memory stores so fixtures can wipe state between tests.
# ---------------------------------------------------------------------------
from src.webinar import main as app_module
from src.webinar.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOM_PAYLOAD = {
    "title": "Intro to FastAPI",
    "speaker": "Alice",
    "start_time": "2025-09-01T10:00:00",
    "status": "pending",
}


def create_room(**overrides) -> dict:
    payload = {**ROOM_PAYLOAD, **overrides}
    r = client.post("/rooms", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Fixture: reset all in-memory stores before every test so tests are isolated.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_storage():
    """Clear all in-memory stores before each test."""
    app_module.rooms.clear()
    app_module.recordings.clear()
    app_module.chat_messages.clear()
    app_module.polls.clear()
    app_module.poll_answers.clear()
    yield


# ===========================================================================
# Root
# ===========================================================================

class TestRoot:
    def test_root_ok(self):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "docs" in data
        assert isinstance(data["endpoints"], list)


# ===========================================================================
# Rooms — CRUD
# ===========================================================================

class TestCreateRoom:
    def test_create_room_success(self):
        r = client.post("/rooms", json=ROOM_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == ROOM_PAYLOAD["title"]
        assert data["speaker"] == ROOM_PAYLOAD["speaker"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_create_room_default_status_is_pending(self):
        payload = {k: v for k, v in ROOM_PAYLOAD.items() if k != "status"}
        r = client.post("/rooms", json=payload)
        assert r.status_code == 201
        assert r.json()["status"] == "pending"

    def test_create_room_active_status(self):
        r = client.post("/rooms", json={**ROOM_PAYLOAD, "status": "active"})
        assert r.status_code == 201
        assert r.json()["status"] == "active"

    def test_create_room_ended_status(self):
        r = client.post("/rooms", json={**ROOM_PAYLOAD, "status": "ended"})
        assert r.status_code == 201
        assert r.json()["status"] == "ended"

    def test_create_room_invalid_status(self):
        r = client.post("/rooms", json={**ROOM_PAYLOAD, "status": "unknown"})
        assert r.status_code == 400
        assert "status" in r.json()["detail"].lower()

    def test_create_room_empty_title(self):
        r = client.post("/rooms", json={**ROOM_PAYLOAD, "title": ""})
        assert r.status_code == 422

    def test_create_room_empty_speaker(self):
        r = client.post("/rooms", json={**ROOM_PAYLOAD, "speaker": ""})
        assert r.status_code == 422

    def test_create_room_missing_start_time(self):
        payload = {k: v for k, v in ROOM_PAYLOAD.items() if k != "start_time"}
        r = client.post("/rooms", json=payload)
        assert r.status_code == 422


class TestGetRoom:
    def test_get_room_success(self):
        room = create_room()
        r = client.get(f"/rooms/{room['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == room["id"]

    def test_get_room_not_found(self):
        r = client.get("/rooms/99999")
        assert r.status_code == 404
        assert "99999" in r.json()["detail"]

    def test_list_rooms_empty(self):
        r = client.get("/rooms")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_rooms_multiple(self):
        create_room(title="Room A")
        create_room(title="Room B")
        r = client.get("/rooms")
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestUpdateRoom:
    def test_update_title(self):
        room = create_room()
        r = client.put(f"/rooms/{room['id']}", json={"title": "Updated Title"})
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Title"

    def test_update_status_to_active(self):
        room = create_room()
        r = client.put(f"/rooms/{room['id']}", json={"status": "active"})
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_update_invalid_status(self):
        room = create_room()
        r = client.put(f"/rooms/{room['id']}", json={"status": "broken"})
        assert r.status_code == 400

    def test_update_room_not_found(self):
        r = client.put("/rooms/99999", json={"title": "Ghost"})
        assert r.status_code == 404

    def test_update_partial_fields(self):
        room = create_room()
        original_speaker = room["speaker"]
        r = client.put(f"/rooms/{room['id']}", json={"title": "New Title"})
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "New Title"
        assert data["speaker"] == original_speaker  # untouched


class TestDeleteRoom:
    def test_delete_room_success(self):
        room = create_room()
        r = client.delete(f"/rooms/{room['id']}")
        assert r.status_code == 204
        # Verify it's gone
        assert client.get(f"/rooms/{room['id']}").status_code == 404

    def test_delete_room_not_found(self):
        r = client.delete("/rooms/99999")
        assert r.status_code == 404

    def test_delete_cascades_chat(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "bob", "message": "hello"})
        client.delete(f"/rooms/{room['id']}")
        # After deletion the room is gone; messages should be cleaned up too.
        assert len(app_module.chat_messages) == 0

    def test_delete_cascades_recordings(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/recordings",
                    json={"video_url": "http://vid.io/1", "duration": 60})
        client.delete(f"/rooms/{room['id']}")
        assert len(app_module.recordings) == 0

    def test_delete_cascades_polls(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/polls",
                    json={"question": "Q?", "options": ["A", "B"]})
        client.delete(f"/rooms/{room['id']}")
        assert len(app_module.polls) == 0


# ===========================================================================
# Chat
# ===========================================================================

class TestChat:
    def test_send_message_success(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/chat",
                        json={"username": "alice", "message": "Hi there!"})
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "alice"
        assert data["message"] == "Hi there!"
        assert data["room_id"] == room["id"]
        assert "timestamp" in data

    def test_send_message_room_not_found(self):
        r = client.post("/rooms/99999/chat",
                        json={"username": "alice", "message": "Hi"})
        assert r.status_code == 404

    def test_send_message_empty_message(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/chat",
                        json={"username": "alice", "message": ""})
        assert r.status_code == 422

    def test_send_message_empty_username(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/chat",
                        json={"username": "", "message": "Hi"})
        assert r.status_code == 422

    def test_get_messages_empty(self):
        room = create_room()
        r = client.get(f"/rooms/{room['id']}/chat")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_messages_multiple(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "alice", "message": "Hello"})
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "bob", "message": "World"})
        r = client.get(f"/rooms/{room['id']}/chat")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_messages_isolation_between_rooms(self):
        room1 = create_room(title="Room 1")
        room2 = create_room(title="Room 2")
        client.post(f"/rooms/{room1['id']}/chat",
                    json={"username": "alice", "message": "Room1 msg"})
        r = client.get(f"/rooms/{room2['id']}/chat")
        assert r.json() == []

    def test_get_messages_room_not_found(self):
        r = client.get("/rooms/99999/chat")
        assert r.status_code == 404


# ===========================================================================
# Polls
# ===========================================================================

class TestPolls:
    def test_create_poll_success(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/polls",
                        json={"question": "Best language?", "options": ["Python", "Go"]})
        assert r.status_code == 201
        data = r.json()
        assert data["question"] == "Best language?"
        assert data["options"] == ["Python", "Go"]
        assert data["room_id"] == room["id"]

    def test_create_poll_room_not_found(self):
        r = client.post("/rooms/99999/polls",
                        json={"question": "?", "options": ["A", "B"]})
        assert r.status_code == 404

    def test_create_poll_single_option_rejected(self):
        room = create_room()
        # Pydantic min_length=2 on the list should reject this
        r = client.post(f"/rooms/{room['id']}/polls",
                        json={"question": "Q?", "options": ["Only one"]})
        assert r.status_code in (400, 422)

    def test_create_poll_empty_question(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/polls",
                        json={"question": "", "options": ["A", "B"]})
        assert r.status_code == 422


class TestPollAnswer:
    def _setup(self):
        room = create_room()
        poll_r = client.post(f"/rooms/{room['id']}/polls",
                             json={"question": "Fav?", "options": ["X", "Y", "Z"]})
        poll = poll_r.json()
        return room, poll

    def test_answer_poll_success(self):
        room, poll = self._setup()
        r = client.post(f"/polls/{poll['id']}/answer",
                        json={"room_id": room["id"], "username": "alice",
                              "selected_option": "X"})
        assert r.status_code == 201
        data = r.json()
        assert data["selected_option"] == "X"
        assert data["username"] == "alice"
        assert data["poll_id"] == poll["id"]

    def test_answer_poll_invalid_option(self):
        room, poll = self._setup()
        r = client.post(f"/polls/{poll['id']}/answer",
                        json={"room_id": room["id"], "username": "alice",
                              "selected_option": "INVALID"})
        assert r.status_code == 400
        assert "Invalid option" in r.json()["detail"]

    def test_answer_poll_not_found(self):
        room = create_room()
        r = client.post("/polls/99999/answer",
                        json={"room_id": room["id"], "username": "alice",
                              "selected_option": "X"})
        assert r.status_code == 404

    def test_answer_poll_wrong_room(self):
        room1 = create_room(title="R1")
        room2 = create_room(title="R2")
        poll_r = client.post(f"/rooms/{room1['id']}/polls",
                             json={"question": "Q?", "options": ["A", "B"]})
        poll = poll_r.json()
        # Submit answer with room2's id — poll belongs to room1
        r = client.post(f"/polls/{poll['id']}/answer",
                        json={"room_id": room2["id"], "username": "alice",
                              "selected_option": "A"})
        assert r.status_code == 400
        assert "does not belong" in r.json()["detail"]

    def test_answer_poll_room_not_found(self):
        room, poll = self._setup()
        r = client.post(f"/polls/{poll['id']}/answer",
                        json={"room_id": 99999, "username": "alice",
                              "selected_option": "X"})
        assert r.status_code == 404


# ===========================================================================
# Recordings
# ===========================================================================

class TestRecordings:
    def test_add_recording_success(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/recordings",
                        json={"video_url": "https://cdn.example.com/rec.mp4",
                              "duration": 3600})
        assert r.status_code == 201
        data = r.json()
        assert data["video_url"] == "https://cdn.example.com/rec.mp4"
        assert data["duration"] == 3600
        assert data["room_id"] == room["id"]
        assert "recorded_at" in data

    def test_add_recording_room_not_found(self):
        r = client.post("/rooms/99999/recordings",
                        json={"video_url": "https://x.com/v.mp4", "duration": 60})
        assert r.status_code == 404

    def test_add_recording_zero_duration_rejected(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/recordings",
                        json={"video_url": "https://x.com/v.mp4", "duration": 0})
        assert r.status_code == 422

    def test_add_recording_negative_duration_rejected(self):
        room = create_room()
        r = client.post(f"/rooms/{room['id']}/recordings",
                        json={"video_url": "https://x.com/v.mp4", "duration": -5})
        assert r.status_code == 422

    def test_get_recordings_empty(self):
        room = create_room()
        r = client.get(f"/rooms/{room['id']}/recordings")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_recordings_multiple(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/recordings",
                    json={"video_url": "https://a.com/1.mp4", "duration": 100})
        client.post(f"/rooms/{room['id']}/recordings",
                    json={"video_url": "https://a.com/2.mp4", "duration": 200})
        r = client.get(f"/rooms/{room['id']}/recordings")
        assert len(r.json()) == 2

    def test_get_recordings_room_not_found(self):
        r = client.get("/rooms/99999/recordings")
        assert r.status_code == 404


# ===========================================================================
# Statistics
# ===========================================================================

class TestStatistics:
    def test_statistics_empty_room(self):
        room = create_room()
        r = client.get(f"/rooms/{room['id']}/statistics")
        assert r.status_code == 200
        data = r.json()
        assert data["participants"] == 0
        assert data["messages"] == 0
        assert data["poll_answers"] == 0
        assert data["polls"] == 0
        assert data["recordings"] == 0

    def test_statistics_counts_messages(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "alice", "message": "Hi"})
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "bob", "message": "Hey"})
        r = client.get(f"/rooms/{room['id']}/statistics")
        assert r.json()["messages"] == 2

    def test_statistics_unique_participants(self):
        room = create_room()
        # alice sends two messages — counts as 1 participant
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "alice", "message": "msg1"})
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "alice", "message": "msg2"})
        client.post(f"/rooms/{room['id']}/chat",
                    json={"username": "bob", "message": "msg3"})
        r = client.get(f"/rooms/{room['id']}/statistics")
        assert r.json()["participants"] == 2

    def test_statistics_counts_polls_and_answers(self):
        room = create_room()
        poll_r = client.post(f"/rooms/{room['id']}/polls",
                             json={"question": "Q?", "options": ["A", "B"]})
        poll = poll_r.json()
        client.post(f"/polls/{poll['id']}/answer",
                    json={"room_id": room["id"], "username": "alice",
                          "selected_option": "A"})
        client.post(f"/polls/{poll['id']}/answer",
                    json={"room_id": room["id"], "username": "bob",
                          "selected_option": "B"})
        r = client.get(f"/rooms/{room['id']}/statistics")
        data = r.json()
        assert data["polls"] == 1
        assert data["poll_answers"] == 2

    def test_statistics_counts_recordings(self):
        room = create_room()
        client.post(f"/rooms/{room['id']}/recordings",
                    json={"video_url": "https://x.com/v.mp4", "duration": 60})
        r = client.get(f"/rooms/{room['id']}/statistics")
        assert r.json()["recordings"] == 1

    def test_statistics_isolation_between_rooms(self):
        room1 = create_room(title="R1")
        room2 = create_room(title="R2")
        client.post(f"/rooms/{room1['id']}/chat",
                    json={"username": "alice", "message": "hi"})
        r = client.get(f"/rooms/{room2['id']}/statistics")
        assert r.json()["messages"] == 0

    def test_statistics_room_not_found(self):
        r = client.get("/rooms/99999/statistics")
        assert r.status_code == 404

    def test_statistics_poll_participants_merged_with_chat(self):
        """User who only answered a poll also counts as a participant."""
        room = create_room()
        poll_r = client.post(f"/rooms/{room['id']}/polls",
                             json={"question": "Q?", "options": ["A", "B"]})
        poll = poll_r.json()
        client.post(f"/polls/{poll['id']}/answer",
                    json={"room_id": room["id"], "username": "charlie",
                          "selected_option": "A"})
        r = client.get(f"/rooms/{room['id']}/statistics")
        assert r.json()["participants"] == 1
