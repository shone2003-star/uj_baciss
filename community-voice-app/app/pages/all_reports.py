"""Page: the admin looks back at every report, whatever its status."""

import httpx
import pandas as pd
import streamlit as st
from components import api
from components.report_view import show_details

st.title("All reports")

try:
    reports = api.get("/reports")
except httpx.HTTPError as error:
    st.error(api.explain(error))
    st.stop()
if not reports:
    st.info("No reports yet.")
    st.stop()

frame = pd.DataFrame(reports)
status = st.selectbox("Status", ["All", *sorted(frame["status"].unique())])
if status != "All":
    frame = frame[frame["status"] == status]

st.caption(f"{len(frame)} reports, newest first (read-only)")
columns = ["id", "created_at", "status", "urgency", "category", "department", "text"]
event = st.dataframe(
    frame[columns],
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="history",
)
rows = event.selection.rows
if rows and rows[0] < len(frame):
    report_id = frame.iloc[rows[0]]["id"]
    if st.button(f"Show details of {report_id}", type="primary"):
        show_details(report_id)
else:
    st.caption("Select a row to see everything known about that report.")
