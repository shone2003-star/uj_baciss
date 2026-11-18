"""Show a conversation. Used by the citizen and the admin pages."""

import streamlit as st

NAMES = {"citizen": "Citizen", "admin": "Municipality"}


def show_messages(messages: list[dict]) -> None:
    """One chat bubble per message. Plain text: a message can never make a link."""
    for message in messages:
        role = "user" if message["sender"] == "citizen" else "assistant"
        with st.chat_message(role):
            st.caption(f"{NAMES[message['sender']]} | {message['created_at']}")
            st.text(message["body"])
