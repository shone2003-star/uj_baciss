"""Contracts for the conversation on a resolved report."""

from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000

Sender = Literal["citizen", "admin"]
ThreadStatus = Literal["open", "closed"]


class Message(BaseModel):
    id: int
    report_id: str
    sender: Sender
    body: str
    created_at: str


class Thread(BaseModel):
    report_id: str
    status: ThreadStatus
    marked_fixed: bool  # the citizen says it is fixed; only the admin closes
    created_at: str
    updated_at: str


class ThreadSummary(Thread):
    """A thread as listed, with a little about its report."""

    text: str  # the report text (already redacted)
    category: str
    urgency: str
    department: str
    message_count: int
    last_sender: Sender
    last_message_at: str
    needs_attention: bool  # open, and the citizen spoke last or marked it fixed


class ReplySuggestion(BaseModel):
    """What the assistant suggests to the admin. Nothing is sent by itself."""

    body: str = Field(
        max_length=MAX_MESSAGE_CHARS,
        description="The next reply to the citizen, in English.",
    )
    looks_resolved: bool = Field(
        description="True only if the citizen clearly says the problem is fixed."
    )
    reason: str = Field(
        description="One sentence: why the thread does or does not look resolved."
    )
