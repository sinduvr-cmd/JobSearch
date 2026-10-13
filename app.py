"""Job Search & Recommendation Application
Main Streamlit Entry Point.
"""

import os
import streamlit as st
from database.connection import init_db, test_connection
from database.repository import get_profile, upsert_jobs_and_skills
from services.api_client import fetch_live_jobs
from services.demo_data import get_curated_demo_jobs
from ui.styles import get_custom_css
from ui.page_search import render_search_page
from ui.page_my_searches import render_my_searches_page
from ui.page_saved_jobs import render_saved_jobs_page
from ui.page_analytics import render_analytics_page
from ui.page_profile import render_profile_page
from ui.page_about import render_about_page

# 1. Streamlit App Configuration
st.set_page_config(
    page_title="Job Search & Recommendation",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Theme Custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# 3. Database Initialization & Health Check
@st.cache_resource(show_spinner=False)
def setup_database():
    try:
        init_db()
        return True, "Connected to MySQL database."
    except Exception as e:
        return False, str(e)

db_ok, db_msg = setup_database()

# 4. Cached API Data Fetcher
@st.cache_data(ttl=600, show_spinner="Fetching latest live jobs from Arbeitnow...")
def get_cached_live_jobs():
    jobs, err = fetch_live_jobs(pages=1)
    if not err and jobs:
        # Cache to MySQL in background
        try:
            upsert_jobs_and_skills(jobs)
        except Exception:
            pass
    return jobs, err

# Session State Navigation Defaults
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Search Jobs"
if "is_demo_mode" not in st.session_state:
    # Default to True so application immediately matches visual benchmark screenshot!
    st.session_state["is_demo_mode"] = True

# Fetch profile
try:
    current_profile = get_profile(profile_id=1)
except Exception:
    current_profile = {
        "id": 1,
        "candidate_name": "Sindhu Suraj",
        "skills": ["Python", "Machine Learning", "SQL", "Data Analysis"],
        "preferred_location": "Bengaluru, India",
        "preferred_work_model": "All",
    }

# -------------------------------------------------------------
# Sidebar Navigation & Filters
# -------------------------------------------------------------
with st.sidebar:
    # Brand Header
    st.markdown("""
    <div class="sidebar-brand-box">
        <div class="sidebar-brand-icon">💼</div>
        <div class="sidebar-brand-title">Job Search &<br/>Recommendation</div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Links
    nav_pages = [
        ("Search Jobs", "🔍"),
        ("My Searches", "📊"),
        ("Saved Jobs", "⭐"),
        ("Analytics", "📈"),
        ("Profile", "👤"),
        ("About", "ℹ️"),
    ]

    for p_name, icon in nav_pages:
        is_active = (st.session_state["current_page"] == p_name)
        active_cls = " active" if is_active else ""
        btn_label = f"{icon}  {p_name}"
        if st.button(
            btn_label,
            key=f"nav_{p_name}",
            type="primary" if is_active else "secondary",
            use_container_width=True
        ):
            st.session_state["current_page"] = p_name
            st.session_state["active_detail_job"] = None
            st.rerun()

    # Data Source / Demo Mode Selection
    st.markdown("<br/>", unsafe_allow_html=True)
    demo_toggle = st.toggle(
        "Demo Mode (Benchmark Data)",
        value=st.session_state["is_demo_mode"],
        help="Toggle between curated benchmark dataset (matching screenshot) and live Arbeitnow public API."
    )
    if demo_toggle != st.session_state["is_demo_mode"]:
        st.session_state["is_demo_mode"] = demo_toggle
        st.session_state["page_number"] = 1
        st.rerun()

    # Filter Results Section
    st.markdown('<div class="sidebar-filter-heading"><span>⚙️ Filter Results</span></div>', unsafe_allow_html=True)

    # 1. Job Type Checkboxes
    st.markdown("<p style='font-size: 13px; font-weight: 700; margin-bottom: 4px; color: #334155;'>Job Type</p>", unsafe_allow_html=True)
    ft = st.checkbox("Full-time", value=True, key="cb_ft")
    pt = st.checkbox("Part-time", value=False, key="cb_pt")
    ct = st.checkbox("Contract", value=False, key="cb_ct")
    it = st.checkbox("Internship", value=False, key="cb_it")

    selected_jts = []
    if ft: selected_jts.append("Full-time")
    if pt: selected_jts.append("Part-time")
    if ct: selected_jts.append("Contract")
    if it: selected_jts.append("Internship")
    st.session_state["filter_job_types"] = selected_jts

    # 2. Work Model Checkboxes
    st.markdown("<p style='font-size: 13px; font-weight: 700; margin-top: 10px; margin-bottom: 4px; color: #334155;'>Work Model</p>", unsafe_allow_html=True)
    rem = st.checkbox("Remote", value=True, key="cb_rem")
    hyb = st.checkbox("Hybrid", value=True if st.session_state["is_demo_mode"] else False, key="cb_hyb")
    ons = st.checkbox("On-site", value=True if st.session_state["is_demo_mode"] else False, key="cb_ons")

    selected_wms = []
    if rem: selected_wms.append("Remote")
    if hyb: selected_wms.append("Hybrid")
    if ons: selected_wms.append("On-site")
    st.session_state["filter_work_models"] = selected_wms

    # 3. Experience Level
    st.markdown("<p style='font-size: 13px; font-weight: 700; margin-top: 10px; margin-bottom: 4px; color: #334155;'>Experience Level</p>", unsafe_allow_html=True)
    exp_level = st.selectbox(
        "Experience Level",
        options=["All Levels", "Entry", "Mid", "Senior", "Lead"],
        label_visibility="collapsed",
        key="sb_exp"
    )
    st.session_state["filter_exp"] = exp_level

    # 4. Salary Range Controls
    st.markdown("<p style='font-size: 13px; font-weight: 700; margin-top: 10px; margin-bottom: 4px; color: #334155;'>Salary Range (USD)</p>", unsafe_allow_html=True)
    sal_range = st.slider(
        "Salary Range (USD)",
        min_value=0,
        max_value=300000,
        value=(0, 300000),
        step=10000,
        format="$%d",
        label_visibility="collapsed",
        key="sl_sal"
    )
    st.session_state["filter_salary"] = sal_range

    inc_unknown = st.checkbox("Include jobs with unknown salary", value=True, key="cb_unknown_sal")
    st.session_state["filter_include_unknown_salary"] = inc_unknown

    # 5. Sort By
    st.markdown("<p style='font-size: 13px; font-weight: 700; margin-top: 10px; margin-bottom: 4px; color: #334155;'>Sort By</p>", unsafe_allow_html=True)
    sort_option = st.selectbox(
        "Sort By",
        options=["Relevance", "Newest", "Salary (High to Low)"],
        label_visibility="collapsed",
        key="sb_sort"
    )
    st.session_state["filter_sort"] = sort_option

    # 6. Reset Filters Action
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("🔄 Reset Filters", use_container_width=True, kind="secondary"):
        st.session_state["filter_job_types"] = ["Full-time"]
        st.session_state["filter_work_models"] = ["Remote", "Hybrid", "On-site"] if st.session_state["is_demo_mode"] else ["Remote"]
        st.session_state["filter_exp"] = "All Levels"
        st.session_state["filter_salary"] = (0, 300000)
        st.session_state["filter_sort"] = "Relevance"
        st.session_state["page_number"] = 1
        st.rerun()

    # DB Connection Status Indicator
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    if db_ok:
        st.markdown("<div style='font-size: 11.5px; color: #16A34A; font-weight: 600;'>🟢 MySQL Persistent DB: Connected</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size: 11.5px; color: #DC2626; font-weight: 600;'>🔴 MySQL Error: {db_msg[:40]}...</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# Main Content Area Page Routing
# -------------------------------------------------------------
current_page = st.session_state["current_page"]

if current_page == "Search Jobs":
    # Load dataset according to mode
    if st.session_state["is_demo_mode"]:
        active_dataset = get_curated_demo_jobs()
    else:
        active_dataset, api_err = get_cached_live_jobs()
        if api_err:
            st.error(f"Live API Notice: {api_err}. Showing cached fallback data.")
            if not active_dataset:
                active_dataset = get_curated_demo_jobs()

    render_search_page(
        profile=current_profile,
        raw_jobs=active_dataset,
        is_demo_mode=st.session_state["is_demo_mode"]
    )

elif current_page == "My Searches":
    render_my_searches_page(profile_id=current_profile.get("id", 1))

elif current_page == "Saved Jobs":
    render_saved_jobs_page(profile_id=current_profile.get("id", 1))

elif current_page == "Analytics":
    render_analytics_page()

elif current_page == "Profile":
    render_profile_page(profile_id=current_profile.get("id", 1))

elif current_page == "About":
    render_about_page()
