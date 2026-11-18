"""Show a streamed run as it happens."""

import httpx
import streamlit as st

from components import api


def watch(path: str, payload: dict, label: str) -> tuple[str | None, str]:
    """Stream a run into a status box. Returns (report id, last event name)."""
    report_id, last, trace = None, "error", []
    with st.status(label, expanded=True) as box:
        lines = st.container()  # finished steps
        waiting = st.empty()  # what runs next, while a slow step is running
        waiting.caption("Starting...")
        try:
            for name, data in api.stream(path, payload):
                last = name
                if name == "started":
                    report_id = data["report_id"]
                elif name == "step":
                    line = f"{data['node']}: {data['message']}"
                    trace.append(line)
                    lines.write(line)
                    waiting.caption(data.get("hint") or "Working...")
                elif name == "error":
                    st.error(data["message"])
                    if data.get("code") == "privacy_unavailable":
                        st.session_state["privacy_down"] = True
        except httpx.HTTPError as error:
            st.error(api.explain(error))
        waiting.empty()
        box.update(label=label, state="error" if last == "error" else "complete")
    st.session_state["trace"] = trace
    return report_id, last
