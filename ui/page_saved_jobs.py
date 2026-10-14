"""Saved Jobs page module.
Displays saved listings persisted in MySQL with ability to view details or remove them.
"""

import html
import streamlit as st
from database.repository import get_saved_jobs_detailed, toggle_saved_job
from ui.components import render_job_card, format_relative_time
from ui.page_search import render_job_details_dialog


def render_saved_jobs_page(profile_id: int = 1):
    st.markdown('<h1 style="color: #1E1B4B; font-size: 26px; font-weight: 800; margin-bottom: 8px;">⭐ Saved Jobs</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 14px; margin-bottom: 24px;">All jobs you have bookmarked, persisted securely in MySQL.</p>', unsafe_allow_html=True)

    # Active detail view modal
    if st.session_state.get("active_detail_job"):
        with st.container():
            render_job_details_dialog(st.session_state["active_detail_job"])
            return

    try:
        saved_jobs = get_saved_jobs_detailed(profile_id=profile_id)
    except Exception as e:
        st.warning(f"⚠️ **Database Disconnected:** Could not retrieve saved jobs from MySQL ({e}). Connect your database to sync saved jobs.")
        saved_jobs = []

    if not saved_jobs:
        st.info("No saved jobs to display. When browsing listings in **Search Jobs**, click the **🤍 Save** button on any card!")
        return

    st.markdown(f"**Total Bookmarked Jobs:** `{len(saved_jobs)}`")
    st.markdown("<br/>", unsafe_allow_html=True)

    for idx, j in enumerate(saved_jobs):
        j_id = j.get("id")

        def make_toggle_handler(target_id):
            def handler(_):
                toggle_saved_job(profile_id=profile_id, job_id=target_id)
                st.rerun()
            return handler

        def make_details_handler(target_job):
            def handler(_):
                st.session_state["active_detail_job"] = target_job
                st.rerun()
            return handler

        render_job_card(
            job=j,
            is_saved=True,
            requested_skills=[],
            on_toggle_save=make_toggle_handler(j_id),
            on_view_details=make_details_handler(j),
            card_index=idx
        )
