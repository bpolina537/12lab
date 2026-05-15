from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from itertools import count

app = FastAPI(title="Webinar Platform API")


@app.get("/", summary="API info")
def root():
    return {
        "message": "Webinar Platform API is running",
        "docs": "/docs",
        "endpoints": [
            "GET  /rooms",
            "POST /rooms",
            "GET  /rooms/{id}",
            "PUT  /rooms/{id}",
            "DELETE /rooms/{id}",
            "POST /rooms/{id}/chat",
            "GET  /rooms/{id}/chat",
            "POST /rooms/{id}/polls",
            "POST /polls/{id}/answer",
            "GET  /rooms/{id}/statistics",
            "POST /rooms/{id}/recordings",
            "GET  /rooms/{id}/recordings",
        ],
    }


# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------
rooms: dict[int, dict] = {}
recordings: dict[int, dict] = {}
chat_messages: dict[int, dict] = {}
polls: dict[int, dict] = {}
poll_answers: dict[int, dict] = {}

room_id_gen = count(1)
recording_id_gen = count(1)
message_id_gen = count(1)
poll_id_gen = count(1)
answer_id_gen = count(1)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RoomCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    speaker: str = Field(..., min_length=1, max_length=100)
    start_time: datetime
    status: str = Field(default="pending")

    def validate_status(self) -> None:
        if self.status not in ("pending", "active", "ended"):
            raise ValueError("status must be pending | active | ended")


class RoomUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    speaker: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[datetime] = None
    status: Optional[str] = None

    def validate_status(self) -> None:
        if self.status is not None and self.status not in ("pending", "active", "ended"):
            raise ValueError("status must be pending | active | ended")


class ChatMessageCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)


class PollCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    options: list[str] = Field(..., min_length=2)


class PollAnswerCreate(BaseModel):
    room_id: int
    username: str = Field(..., min_length=1, max_length=100)
    selected_option: str = Field(..., min_length=1)


class RecordingCreate(BaseModel):
    video_url: str = Field(..., min_length=1)
    duration: int = Field(..., gt=0, description="Duration in seconds")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_room_or_404(room_id: int) -> dict:
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return rooms[room_id]


def get_poll_or_404(poll_id: int) -> dict:
    if poll_id not in polls:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")
    return polls[poll_id]

# ---------------------------------------------------------------------------
# Rooms CRUD
# ---------------------------------------------------------------------------

@app.get("/rooms", summary="List all rooms")
def list_rooms():
    return list(rooms.values())


@app.post("/rooms", status_code=201, summary="Create a room")
def create_room(body: RoomCreate):
    try:
        body.validate_status()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    rid = next(room_id_gen)
    room = {
        "id": rid,
        "title": body.title,
        "speaker": body.speaker,
        "start_time": body.start_time.isoformat(),
        "status": body.status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rooms[rid] = room
    return room


@app.get("/rooms/{room_id}", summary="Get a room by id")
def get_room(room_id: int):
    return get_room_or_404(room_id)


@app.put("/rooms/{room_id}", summary="Update a room")
def update_room(room_id: int, body: RoomUpdate):
    try:
        body.validate_status()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    room = get_room_or_404(room_id)
    if body.title is not None:
        room["title"] = body.title
    if body.speaker is not None:
        room["speaker"] = body.speaker
    if body.start_time is not None:
        room["start_time"] = body.start_time.isoformat()
    if body.status is not None:
        room["status"] = body.status
    return room


@app.delete("/rooms/{room_id}", status_code=204, summary="Delete a room")
def delete_room(room_id: int):
    get_room_or_404(room_id)
    del rooms[room_id]
    # Cascade-delete related data
    for store in (recordings, chat_messages, polls, poll_answers):
        keys_to_delete = [k for k, v in store.items() if v.get("room_id") == room_id]
        for k in keys_to_delete:
            del store[k]

# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@app.post("/rooms/{room_id}/chat", status_code=201, summary="Send a chat message")
def send_message(room_id: int, body: ChatMessageCreate):
    get_room_or_404(room_id)
    mid = next(message_id_gen)
    msg = {
        "id": mid,
        "room_id": room_id,
        "username": body.username,
        "message": body.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    chat_messages[mid] = msg
    return msg


@app.get("/rooms/{room_id}/chat", summary="Get all chat messages for a room")
def get_messages(room_id: int):
    get_room_or_404(room_id)
    return [m for m in chat_messages.values() if m["room_id"] == room_id]

# ---------------------------------------------------------------------------
# Polls
# ---------------------------------------------------------------------------

@app.post("/rooms/{room_id}/polls", status_code=201, summary="Create a poll")
def create_poll(room_id: int, body: PollCreate):
    get_room_or_404(room_id)
    if len(body.options) < 2:
        raise HTTPException(status_code=400, detail="A poll needs at least 2 options")
    pid = next(poll_id_gen)
    poll = {
        "id": pid,
        "room_id": room_id,
        "question": body.question,
        "options": body.options,
    }
    polls[pid] = poll
    return poll


@app.post("/polls/{poll_id}/answer", status_code=201, summary="Answer a poll")
def answer_poll(poll_id: int, body: PollAnswerCreate):
    poll = get_poll_or_404(poll_id)
    get_room_or_404(body.room_id)

    if poll["room_id"] != body.room_id:
        raise HTTPException(status_code=400, detail="Poll does not belong to the specified room")
    if body.selected_option not in poll["options"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid option. Choose one of: {poll['options']}",
        )

    aid = next(answer_id_gen)
    answer = {
        "id": aid,
        "poll_id": poll_id,
        "room_id": body.room_id,
        "username": body.username,
        "selected_option": body.selected_option,
    }
    poll_answers[aid] = answer
    return answer

# ---------------------------------------------------------------------------
# Recordings
# ---------------------------------------------------------------------------

@app.post("/rooms/{room_id}/recordings", status_code=201, summary="Add a recording")
def add_recording(room_id: int, body: RecordingCreate):
    get_room_or_404(room_id)
    rid = next(recording_id_gen)
    rec = {
        "id": rid,
        "room_id": room_id,
        "video_url": body.video_url,
        "duration": body.duration,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    recordings[rid] = rec
    return rec


@app.get("/rooms/{room_id}/recordings", summary="Get recordings for a room")
def get_recordings(room_id: int):
    get_room_or_404(room_id)
    return [r for r in recordings.values() if r["room_id"] == room_id]

# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@app.get("/rooms/{room_id}/statistics", summary="Get room statistics")
def get_statistics(room_id: int):
    get_room_or_404(room_id)

    room_polls = [p for p in polls.values() if p["room_id"] == room_id]
    room_poll_ids = {p["id"] for p in room_polls}

    messages_count = sum(1 for m in chat_messages.values() if m["room_id"] == room_id)
    answers_count = sum(1 for a in poll_answers.values() if a["poll_id"] in room_poll_ids)
    # Unique participants = union of chat usernames + poll answer usernames
    chat_users = {m["username"] for m in chat_messages.values() if m["room_id"] == room_id}
    poll_users = {a["username"] for a in poll_answers.values() if a["poll_id"] in room_poll_ids}
    participants = len(chat_users | poll_users)

    return {
        "room_id": room_id,
        "participants": participants,
        "messages": messages_count,
        "poll_answers": answers_count,
        "polls": len(room_polls),
        "recordings": sum(1 for r in recordings.values() if r["room_id"] == room_id),
    }
