"""Page 2: a reviewer checks reports, then the drafted reply."""

import httpx
import streamlit as st
from components import api, live
from components.queue_view import ALL, SORTS, apply_view, keep_valid
from components.report_view import show_report

from community_voice.schemas.triage import Category, Urgency

st.title("Review queue")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

try:
    queue = api.get("/reviews")
except httpx.HTTPError as error:
    st.error(api.explain(error))
    st.stop()
if not queue:
    st.info("Nothing is waiting for review.")
    st.stop()

# Arriving from the dashboard: show that report, with no filter in the way.
target = st.session_state.pop("review_open", None)
if target in {r["id"] for r in queue}:
    st.session_state.update(
        queue_sort=SORTS[0],
        queue_urgency=ALL,
        queue_category=ALL,
        queue_status=ALL,
        review_pick=target,
    )

statuses = sorted({r["status"] for r in queue})
for key, options in {
    "queue_urgency": [ALL, *(u.value for u in Urgency)],
    "queue_category": [ALL, *(c.value for c in Category)],
    "queue_status": [ALL, *statuses],
}.items():
    keep_valid(key, options)
sort_box, urgency_box, category_box, status_box = st.columns(4)
sort = sort_box.selectbox("Sort", SORTS, key="queue_sort")
urgency = urgency_box.selectbox(
    "Urgency", [ALL, *(u.value for u in Urgency)], key="queue_urgency"
)
category = category_box.selectbox(
    "Category", [ALL, *(c.value for c in Category)], key="queue_category"
)
status = status_box.selectbox(
    "Status",
    [ALL, *statuses],
    key="queue_status",
    format_func=lambda s: s.replace("_", " "),
)
shown = apply_view(queue, sort, urgency, category, status)
st.caption(f"{len(shown)} of {len(queue)} reports")
if not shown:
    st.info("No reports match these filters.")
    st.stop()

by_id = {r["id"]: r for r in shown}


def queue_label(report_id: str) -> str:
    r = by_id[report_id]
    stopped = "STOPPED | " if r.get("stopped_at") else ""
    return (
        f"{stopped}{r['urgency'].upper()} | {r['category']} | "
        f"{r['status']} | {report_id}"
    )


keep_valid("review_pick", list(by_id))
report_id = st.selectbox(
    "Report", list(by_id), format_func=queue_label, key="review_pick"
)
detail = api.get(f"/reports/{report_id}")

if detail["stopped_at"]:
    st.warning(
        f"This report stopped while {detail['stopped_at']}. Nothing was lost: "
        "press Retry to run that step again."
    )
    if st.button("Retry", type="primary"):
        live.watch(f"/reports/{report_id}/retry", {}, "Retrying")
        detail = api.get(f"/reports/{report_id}")

if detail["waiting_for"] == "review":
    p = detail["pending"]
    triage, routing = p["triage"], p["routing"]
    show_report(p, report_id, detail["has_photo"])

    categories, urgencies = [c.value for c in Category], [u.value for u in Urgency]
    with st.form("review"):
        action = st.radio("Decision", ["approve", "reject"], horizontal=True)
        category = st.selectbox(
            "Category", categories, index=categories.index(triage["category"])
        )
        urgency = st.selectbox(
            "Urgency", urgencies, index=urgencies.index(triage["urgency"])
        )
        department = st.text_input("Department", routing["department"])
        note = st.text_area("Note (optional)")
        sent = st.form_submit_button("Send decision", type="primary")
    if sent:
        decision = {"action": action, "note": note}
        if category != triage["category"]:
            decision["category"] = category
        if urgency != triage["urgency"]:
            decision["urgency"] = urgency
        if department != routing["department"]:
            decision["department"] = department
        live.watch(f"/reports/{report_id}/review", decision, "Decision sent")
        detail = api.get(f"/reports/{report_id}")

if detail["waiting_for"] == "draft":
    draft = detail["pending"]["draft"]
    st.subheader("Draft reply")
    with st.form("draft"):
        edited = st.text_area("Reply to the citizen", draft["body"], height=260)
        approve = st.form_submit_button("Approve", type="primary")
        reject = st.form_submit_button("Reject")
    if approve or reject:
        decision = {"action": "approve" if approve else "reject"}
        if approve and edited != draft["body"]:
            decision["text"] = edited
        try:
            result = api.send("POST", f"/reports/{report_id}/draft", json=decision)
        except httpx.HTTPError as error:
            st.error(api.explain(error))
        else:
            st.session_state.flash = f"{report_id}: {result['status']}"
            st.rerun()
