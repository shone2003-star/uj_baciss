"""Turns a graph run into a stream of events."""

import logging
from collections.abc import Iterator
from typing import Any

from fastapi.sse import ServerSentEvent

from community_voice.api.schemas import (
    DoneEvent,
    ErrorEvent,
    PausedEvent,
    StepEvent,
)
from community_voice.db.repository import delete_owner, get_report

logger = logging.getLogger(__name__)

# The graph step a paused report is waiting in, and what the caller should do.
WAITING = {"human_review": "review", "draft_review": "draft"}


# Plain words for the step a run stopped at.
STEP_LABELS = {
    "triage": "reading the report",
    "routing": "finding the department",
    "context_check": "checking the web",
    "duplicate_check": "checking for similar reports",
    "save_report": "saving the report",
    "known_outage": "saving the report",
    "finish_review": "saving the decision",
    "drafter": "writing the draft reply",
    "finish_draft": "saving the reply",
}


def thread_config(report_id: str) -> dict:
    return {"configurable": {"thread_id": report_id}}


def stopped_step(snapshot: Any) -> str | None:
    """Where a run stopped after an error or a crash, in plain words.

    Unfinished work with no question waiting for a person means it stopped.
    """
    if not snapshot.next or snapshot.interrupts or snapshot.next[0] in WAITING:
        return None
    return STEP_LABELS.get(snapshot.next[0], snapshot.next[0])


# What runs next after each step, so the screen is not silent during a slow one.
HINTS = {
    "privacy": "Reading the report and choosing a category and urgency...",
    "triage": "Finding the responsible department...",
    "routing": "Checking for known outages and similar reports...",
    "context_check": "Checking for similar reports...",
    "duplicate_check": "Saving the report...",
    "human_review": "Saving the decision...",
}
DRAFTING_HINT = "Writing the draft reply with AI (about 10 seconds)..."


def next_hint(node: str, update: dict) -> str | None:
    if node == "finish_review" and update.get("status") == "approved":
        return DRAFTING_HINT  # the Drafter is the slowest step
    return HINTS.get(node)


def describe(node: str, update: dict) -> str:
    """A short plain-language line for a finished step."""
    if node == "triage":
        triaged = update["triage_result"]
        return f"{triaged.category.value}, {triaged.urgency.value} urgency"
    if node == "routing":
        return update["routing_result"].department
    if node == "context_check":
        return update["context_result"].finding.value
    if node == "duplicate_check":
        duplicate = update["duplicate_result"].duplicate_of
        return f"duplicate of {duplicate}" if duplicate else "no duplicate"
    if node == "human_review":
        return f"reviewer chose to {update['review'].action}"
    if node == "draft_review":
        return f"reviewer chose to {update['draft_decision'].action}"
    if node in ("known_outage", "finish_review", "finish_draft"):
        return update["status"]
    if node == "save_report":
        return "saved"
    if node == "drafter":
        return "draft written"
    return "done"


def stream_run(
    graph: Any, graph_input: Any, report_id: str, show_payload: bool = True
) -> Iterator[ServerSentEvent]:
    """Run the graph and yield one event per finished step, then pause or done.

    show_payload=False leaves out what the reviewer sees (for citizens).
    """
    config = thread_config(report_id)
    try:
        for chunk in graph.stream(
            graph_input, config, stream_mode="updates", version="v2"
        ):
            if chunk["type"] != "updates":
                continue
            for node, update in chunk["data"].items():
                if node == "__interrupt__":
                    continue
                update = update or {}
                step = StepEvent(
                    node=node,
                    message=describe(node, update),
                    hint=next_hint(node, update),
                )
                yield ServerSentEvent(data=step, event="step")
        snapshot = graph.get_state(config)
        if snapshot.next:
            paused = PausedEvent(
                waiting_for=WAITING[snapshot.next[0]],
                payload=snapshot.interrupts[0].value if show_payload else None,
            )
            yield ServerSentEvent(data=paused, event="paused")
        else:
            done = DoneEvent(status=snapshot.values["status"])
            yield ServerSentEvent(data=done, event="done")
    except Exception:
        # Details stay in the server log; the caller only learns what to do next.
        logger.exception("Workflow failed for %s", report_id)
        if get_report(report_id) is None:  # never saved: nothing to retry
            delete_owner(report_id)
            failure = ErrorEvent(
                message="Your report was not saved. Please send it again.",
                code="not_saved",
            )
        else:  # saved, so an admin can run the failed step again
            failure = ErrorEvent(
                message="A step failed. The report is kept: open it and press Retry.",
                code="stopped",
            )
        yield ServerSentEvent(data=failure, event="error")
