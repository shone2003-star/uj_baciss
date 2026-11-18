"""Page: a citizen follows the conversation about a resolved report."""

import httpx
import streamlit as st
from components import api, chat

st.title("Messages")

if "chat_error" in st.session_state:
    st.error(st.session_state.pop("chat_error"))

try:
    threads = api.get("/my/threads")
except httpx.HTTPError as error:
    st.error(api.explain(error))
    st.stop()
if not threads:
    st.info("No conversations yet. One opens when your report has a reply.")
    st.stop()

by_id = {t["report_id"]: t for t in threads}


def thread_label(report_id: str) -> str:
    thread = by_id[report_id]
    return f"{report_id} | {thread['status']} | {thread['text'][:50]}"


report_id = st.selectbox("Report", list(by_id), format_func=thread_label)
try:
    detail = api.get(f"/threads/{report_id}")
except httpx.HTTPError as error:
    st.error(api.explain(error))
    st.stop()
thread = detail["thread"]

st.button("Refresh")
chat.show_messages(detail["messages"])

if thread["status"] == "closed":
    st.info("The municipality closed this conversation. You can still read it.")
    st.stop()

if thread["marked_fixed"]:
    st.info("You said this is fixed. The municipality will close the conversation.")
elif st.button("Mark as fixed"):
    try:
        api.send("POST", f"/threads/{report_id}/fixed")
    except httpx.HTTPError as error:
        st.error(api.explain(error))
    else:
        st.rerun()

# The text box is emptied only after a message was sent (a new key gives a new box).
version = st.session_state.get("chat_version", 0)
filter_down = st.session_state.get("chat_privacy_down", False)
with st.form("message"):
    body = st.text_area("Your message", max_chars=1000, key=f"body_{version}")
    agreed = False
    if filter_down:
        agreed = st.checkbox(
            "The local privacy filter (Ollama) is not available, so my personal "
            "details may be sent to the AI services. Only phone numbers, ID numbers "
            "and emails will be removed. I agree to continue.",
            key="chat_allow_unfiltered",
        )
    sent = st.form_submit_button("Send", type="primary")

if sent and body.strip():
    try:
        api.send(
            "POST",
            f"/threads/{report_id}/messages",
            json={"body": body, "allow_unfiltered": agreed},
        )
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 503:  # only the privacy filter can cause this
            st.session_state.chat_privacy_down = True
            st.session_state.chat_error = (
                "The local privacy filter could not be reached. "
                "Tick the box to continue without it, then send again."
            )
        else:
            st.session_state.chat_error = api.explain(error)
        st.rerun()
    except httpx.HTTPError as error:
        st.error(api.explain(error))
    else:
        st.session_state.chat_privacy_down = False
        st.session_state.chat_version = version + 1
        st.rerun()
