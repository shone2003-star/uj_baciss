"""Page: the admin follows the conversations, gets suggestions, replies and closes."""

import httpx
import streamlit as st
from components import api, chat
from components.report_view import show_details

FILTERS = {
    "Needs attention": "?attention=true",
    "Open": "?status=open",
    "Closed": "?status=closed",
    "All": "",
}

st.title("Conversations")

if "conv_flash" in st.session_state:
    kind, message = st.session_state.pop("conv_flash")
    getattr(st, kind)(message)


def send_reply(report_id: str) -> None:
    """Runs before the page is drawn again, so it may empty the text box."""
    key = f"reply_{report_id}"
    body = st.session_state.get(key, "").strip()
    if not body:
        st.session_state.conv_flash = ("warning", "Write a reply first.")
        return
    try:
        api.send("POST", f"/threads/{report_id}/messages", json={"body": body})
    except httpx.HTTPError as error:
        st.session_state.conv_flash = ("error", api.explain(error))
    else:
        st.session_state[key] = ""
        st.session_state.conv_flash = ("success", "Reply sent.")


def close(report_id: str) -> None:
    try:
        api.send("POST", f"/threads/{report_id}/close")
    except httpx.HTTPError as error:
        st.session_state.conv_flash = ("error", api.explain(error))
    else:
        st.session_state.conv_flash = ("success", f"{report_id} is closed.")


choice = st.radio("Show", list(FILTERS), horizontal=True)
try:
    threads = api.get("/threads" + FILTERS[choice])
except httpx.HTTPError as error:
    st.error(api.explain(error))
    st.stop()
if not threads:
    st.info("No conversations here.")
    st.stop()

by_id = {t["report_id"]: t for t in threads}


def thread_label(report_id: str) -> str:
    t = by_id[report_id]
    mark = "NEW | " if t["needs_attention"] else ""
    return (
        f"{mark}{t['urgency'].upper()} | {t['category']} | {t['status']} | {report_id}"
    )


report_id = st.selectbox("Report", list(by_id), format_func=thread_label)
try:
    detail = api.get(f"/threads/{report_id}")
except httpx.HTTPError as error:
    st.error(api.explain(error))
    st.stop()
thread = detail["thread"]

st.caption("Report (personal details already removed)")
st.text(detail["report_text"])
if st.button("Report details"):
    show_details(report_id)
st.button("Refresh")
chat.show_messages(detail["messages"])

if thread["status"] == "closed":
    st.info("This conversation is closed. Nobody can write in it.")
    st.stop()

if thread["marked_fixed"]:
    st.warning("The citizen says it is fixed. Close the conversation if you agree.")

if st.button("Suggest reply"):
    with st.spinner("The assistant is reading the conversation..."):
        try:
            suggestion = api.send("POST", f"/threads/{report_id}/suggest")
        except httpx.HTTPError as error:
            st.error(api.explain(error))
        else:
            st.session_state[f"reply_{report_id}"] = suggestion["body"]
            st.session_state.suggestion = {"id": report_id, **suggestion}

note = st.session_state.get("suggestion")
if note and note["id"] == report_id:
    verdict = "Looks resolved" if note["looks_resolved"] else "Does not look resolved"
    st.caption(f"Assistant: {verdict}. {note['reason']} Check and edit before sending.")

st.text_area(
    "Reply to the citizen", max_chars=1000, height=160, key=f"reply_{report_id}"
)
st.button("Send reply", type="primary", on_click=send_reply, args=(report_id,))

st.divider()
sure = st.checkbox(
    "I want to close this conversation. Nobody can write in it afterwards.",
    key=f"sure_{report_id}",
)
st.button("Close conversation", disabled=not sure, on_click=close, args=(report_id,))
