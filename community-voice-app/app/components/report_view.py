"""Show what the agents found about a report: on the review page and in a dialog."""

import httpx
import streamlit as st

from components import api


def show_report(p: dict, report_id: str, has_photo: bool) -> None:
    """p has text, triage, routing, context and duplicate (as the API sends them)."""
    triage, routing, context = p["triage"], p["routing"], p["context"]
    st.subheader("Report")
    st.write(p["text"])
    if triage["language"] != "en":
        st.caption(f"Translation ({triage['language']}): {triage['english_text']}")
    st.write(f"**Summary:** {triage['summary']}")
    st.write(f"**Urgency:** {triage['urgency']}: {triage['urgency_reason']}")
    st.write(
        f"**Routing:** {routing['municipality']}, {routing['department']}: "
        f"{routing['reason']}"
    )
    if context:
        st.write(f"**Web check:** {context['finding']}: {context['summary']}")
        for source in context["sources"]:
            st.markdown(f"- [{source['title']}]({source['url']})")
    if p["duplicate"]["duplicate_of"]:
        st.write(f"**Possible duplicate of:** {p['duplicate']['duplicate_of']}")
    if has_photo:
        st.image(api.get_bytes(f"/reports/{report_id}/photo"), width=400)


@st.dialog("Report details", width="large")
def show_details(report_id: str) -> None:
    """A read-only window with everything known about a report (any status)."""
    try:
        detail = api.get(f"/reports/{report_id}")
    except httpx.HTTPError as error:
        st.error(api.explain(error))
        return
    record, details = detail["report"], detail["details"]
    st.caption(f"{record['id']} | {record['status']} | {record['created_at']}")
    if details is None:
        st.write(record["text"])
        st.info("The agents' findings are not available for this report.")
    else:
        show_report({"text": record["text"], **details}, report_id, detail["has_photo"])
        if details["reviews"]:
            st.subheader("Review decisions")
            for review in details["reviews"]:
                changes = [
                    f"{name}: {review[name]}"
                    for name in ("category", "urgency", "department")
                    if review[name]
                ]
                note = f" Note: {review['note']}" if review["note"] else ""
                st.write(
                    f"**{review['action']}** ({review['created_at']})"
                    f" {', '.join(changes)}.{note}"
                )
    if detail["draft"]:
        st.subheader("Reply")
        st.write(detail["draft"])
