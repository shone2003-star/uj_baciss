"""Sort and filter the review queue (the queue is small, so this runs in the page)."""

import streamlit as st

ALL = "All"
SORTS = ["Most urgent first", "Newest first", "Oldest first"]


def apply_view(
    queue: list[dict],
    sort: str = SORTS[0],
    urgency: str = ALL,
    category: str = ALL,
    status: str = ALL,
) -> list[dict]:
    """The reports that match the filters, in the chosen order."""
    kept = [
        r
        for r in queue
        if urgency in (ALL, r["urgency"])
        and category in (ALL, r["category"])
        and status in (ALL, r["status"])
    ]
    if sort == "Newest first":
        return sorted(kept, key=lambda r: r["created_at"], reverse=True)
    if sort == "Oldest first":
        return sorted(kept, key=lambda r: r["created_at"])
    return kept  # the API already sorts by urgency, then oldest first


def keep_valid(key: str, options: list) -> None:
    """Forget a remembered choice that is no longer one of the options."""
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
