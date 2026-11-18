"""Conversations about resolved reports."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from community_voice.api.dependencies import (
    AdminUser,
    AssistantDep,
    CurrentUser,
    can_see,
)
from community_voice.api.schemas import MyThread, NewMessage, ThreadDetail
from community_voice.db.repository import (
    ThreadClosed,
    ThreadFull,
    ThreadNotFound,
    add_message,
    close_thread,
    get_report,
    get_thread,
    list_messages,
    list_threads,
    list_threads_of,
    mark_fixed,
)
from community_voice.privacy.redact import PrivacyFilterError, protect
from community_voice.schemas.chat import (
    Message,
    ReplySuggestion,
    Thread,
    ThreadStatus,
    ThreadSummary,
)
from community_voice.schemas.review import ReportRecord
from community_voice.schemas.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


def _visible(report_id: str, user: User) -> Thread:
    """The thread, or 404 (also for someone else's thread, so ids reveal nothing)."""
    thread = get_thread(report_id)
    if thread is None or not can_see(report_id, user):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return thread


def _open(report_id: str, user: User) -> None:
    """404 if not visible, 409 if the admin closed it."""
    if _visible(report_id, user).status == "closed":
        raise HTTPException(status_code=409, detail="This conversation is closed.")


@router.get("/threads")
def threads(
    admin: AdminUser,
    status: Annotated[ThreadStatus | None, Query()] = None,
    attention: bool = False,
) -> list[ThreadSummary]:
    """Every conversation. attention=true: the citizen spoke last or marked it fixed."""
    return list_threads(status, attention)


@router.get("/my/threads")
def my_threads(user: CurrentUser) -> list[MyThread]:
    """The signed-in person's conversations. A citizen never sees the AI's results."""
    fields = set(MyThread.model_fields)
    return [MyThread(**t.model_dump(include=fields)) for t in list_threads_of(user.id)]


@router.get("/threads/{report_id}")
def read_thread(report_id: str, user: CurrentUser) -> ThreadDetail:
    thread = _visible(report_id, user)
    report = get_report(report_id)
    return ThreadDetail(
        thread=thread,
        report_text=report.text if report else "",
        messages=list_messages(report_id),
    )


@router.post("/threads/{report_id}/messages", status_code=201)
def send_message(report_id: str, message: NewMessage, user: CurrentUser) -> Message:
    """A citizen's text is made private first (503 if the local filter is down)."""
    _open(report_id, user)
    body, sender = message.body, "admin"
    if user.role != "admin":
        sender = "citizen"
        try:
            body = protect(body, message.allow_unfiltered).text
        except PrivacyFilterError:
            detail = "The local privacy filter (Ollama) could not be reached."
            raise HTTPException(status_code=503, detail=detail) from None
    try:
        return add_message(report_id, sender, body)
    except ThreadClosed:  # closed between the check and the write
        raise HTTPException(
            status_code=409, detail="This conversation is closed."
        ) from None
    except ThreadFull:
        detail = "This conversation has reached its message limit."
        raise HTTPException(status_code=409, detail=detail) from None
    except ThreadNotFound:
        raise HTTPException(status_code=404, detail="Conversation not found.") from None


@router.post("/threads/{report_id}/fixed")
def say_fixed(report_id: str, user: CurrentUser) -> Thread:
    """The citizen says it is fixed. The admin decides when to close."""
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Only the citizen can say this.")
    _open(report_id, user)
    mark_fixed(report_id)
    return _visible(report_id, user)


@router.post("/threads/{report_id}/suggest")
def suggest(
    report_id: str, admin: AdminUser, assistant: AssistantDep
) -> ReplySuggestion:
    """The assistant's suggested reply. It is not saved: the admin edits and sends."""
    _open(report_id, admin)
    report: ReportRecord | None = get_report(report_id)
    try:
        return assistant(report, list_messages(report_id))
    except Exception:
        logger.exception("Chat assistant failed for %s", report_id)
        raise HTTPException(status_code=502, detail="The assistant failed.") from None


@router.post("/threads/{report_id}/close")
def close(report_id: str, admin: AdminUser) -> Thread:
    """Close the conversation. Nobody can write in it afterwards."""
    _open(report_id, admin)
    close_thread(report_id)
    return _visible(report_id, admin)
