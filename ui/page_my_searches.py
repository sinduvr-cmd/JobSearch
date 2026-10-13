"""My Searches page module.
Displays search history persisted in MySQL with ability to re-run previous queries.
"""

import html
import streamlit as st
from datetime import datetime
from database.repository import get_recent_searches
from ui.components import format_relative_time


def render_my_searches_page(profile_id: int = 1):
    st.markdown('<h1 style="color: #1E1B4B; font-size: 26px; font-weight: 800; margin-bottom: 8px;">📊 My Search History</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 14px; margin-bottom: 24px;">View your past searches persisted in MySQL. Click <b>Re-run</b> on any search to load its criteria instantly.</p>', unsafe_allow_html=True)

    try:
        searches = get_recent_searches(profile_id=profile_id, limit=50)
    except Exception as e:
        st.error(f"Failed to load search history from database: {e}")
        return

    if not searches:
        st.info("No search history found yet. Run your first search from the **Search Jobs** tab!")
        return

    st.markdown(f"**Total Past Searches Recorded:** `{len(searches)}`")
    st.markdown("<br/>", unsafe_allow_html=True)

    for idx, s in enumerate(searches):
        q = s.get("query") or "All Jobs"
        loc = s.get("location") or "Any Location"
        res_count = s.get("result_count", 0)
        ts = s.get("timestamp")
        time_str = format_relative_time(ts)
        filters = s.get("filters") or {}

        with st.container():
            st.markdown(f"""
            <div class="job-card" style="padding: 16px 20px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0 0 6px 0; color: #0F172A; font-size: 16px; font-weight: 700;">
                            🔍 {html.escape(q)}
                        </h4>
                        <div style="font-size: 13px; color: #64748B;">
                            <span>📍 Location: <b>{html.escape(loc)}</b></span> &nbsp;•&nbsp;
                            <span>📋 Results Found: <b>{res_count}</b></span> &nbsp;•&nbsp;
                            <span>⏱️ {time_str}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_info, c_action = st.columns([5, 1])
            with c_action:
                if st.button("🔄 Re-run Search", key=f"btn_rerun_page_{s.get('id')}_{idx}", type="primary"):
                    st.session_state["search_query"] = s.get("query") or ""
                    st.session_state["search_location"] = s.get("location") or ""
                    if "work_models" in filters and filters["work_models"]:
                        st.session_state["filter_work_models"] = filters["work_models"]
                    if "job_types" in filters and filters["job_types"]:
                        st.session_state["filter_job_types"] = filters["job_types"]
                    st.session_state["page_number"] = 1
                    st.session_state["current_page"] = "Search Jobs"
                    st.rerun()
