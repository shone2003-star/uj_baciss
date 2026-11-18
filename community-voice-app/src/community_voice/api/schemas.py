"""Models for what the API sends back."""

from typing import Annotated, Any

from pydantic import BaseModel, StringConstraints

from community_voice.schemas.chat import MAX_MESSAGE_CHARS, Message, Sender, Thread
from community_voice.schemas.context_check import ContextCheckResult
from community_voice.schemas.duplicate import DuplicateResult
from community_voice.schemas.report import ReportIn
from community_voice.schemas.review import ReportRecord
from community_voice.schemas.routing import RoutingResult
from community_voice.schemas.triage import TriageResult


class NewReport(ReportIn):
    """A report from a citizen, plus their consent to skip the local privacy model."""

    allow_unfiltered: bool = False


class NewMessage(BaseModel):
    """A message in a conversation. allow_unfiltered only matters for a citizen."""

    body: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_CHARS
        ),
    ]
    allow_unfiltered: bool = False


class MyThread(Thread):
    """A citizen's conversation in a list: no category, urgency or department."""

    text: str
    message_count: int
    last_sender: Sender
    last_message_at: str


class ThreadDetail(BaseModel):
    thread: Thread
    report_text: str
    messages: list[Message]


class StartedEvent(BaseModel):
    report_id: str


class StepEvent(BaseModel):
    node: str
    message: str
    hint: str | None = None  # what runs next, shown while waiting


class PausedEvent(BaseModel):
    waiting_for: str  # "review" or "draft"
    payload: Any  # what the reviewer needs to see


class DoneEvent(BaseModel):
    status: str


class ErrorEvent(BaseModel):
    message: str
    code: str | None = None  # "privacy_unavailable": the client may ask for consent


class QueueItem(ReportRecord):
    """A report in the review queue. stopped_at: where a failed run stopped."""

    stopped_at: str | None = None


class ReviewNote(BaseModel):
    """One decision a reviewer made about the report."""

    action: str
    category: str | None
    urgency: str | None
    department: str | None
    note: str
    created_at: str


class ReportDetails(BaseModel):
    """What the agents found out, for any report (also one that is finished)."""

    triage: TriageResult
    routing: RoutingResult
    context: ContextCheckResult | None
    duplicate: DuplicateResult
    reviews: list[ReviewNote]


class ReportDetail(BaseModel):
    report: ReportRecord
    waiting_for: str | None = None
    pending: Any = None
    draft: str | None = None
    has_photo: bool = False
    details: ReportDetails | None = None  # None when the saved workflow state is gone
    stopped_at: str | None = None  # set when a step failed: an admin can retry


# What a citizen is told, whatever the internal status is.
STAGES = {
    "ready_for_review": "Received, waiting for review",
    "fast_track": "Received, waiting for review",
    "duplicate": "Received, waiting for review",
    "needs_human": "Received, waiting for review",
    "approved": "Reviewed, reply being prepared",
    "draft_rejected": "Reviewed. A reply will follow",
    "ready_to_send": "Resolved: see the reply",
    "known_planned_outage": "Known planned outage in your area",
    "rejected": "Closed",
}


class MyReport(BaseModel):
    """What a citizen sees of their own report."""

    id: str
    text: str
    status: str
    stage: str  # the status in plain words
    reply: str | None  # the approved reply, once there is one
    created_at: str
    has_photo: bool


class PhotoOutcome(BaseModel):
    report_id: str
    size: int  # bytes stored


class SampleOut(BaseModel):
    id: str
    language: str
    text: str


class DraftOutcome(BaseModel):
    report_id: str
    status: str
    draft: str
