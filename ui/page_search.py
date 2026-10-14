"""Search Jobs page module.
Coordinates search panel, filter execution, ranking, pagination, details modal,
and right-column insights.
"""

import html
import streamlit as st
from typing import List, Dict, Any, Set
from services.ranker import rank_jobs
from services.normalizer import normalize_skill_query
from database.repository import (
    upsert_jobs_and_skills,
    save_search_transaction,
    toggle_saved_job,
    get_saved_job_ids,
    get_recent_searches,
)
from ui.components import (
    render_hero_banner,
    render_job_card,
    render_top_skills_chart,
    render_job_type_donut,
    render_recent_searches_widget,
)


def apply_local_filters(
    jobs: List[Dict[str, Any]],
    selected_job_types: List[str],
    selected_work_models: List[str],
    selected_exp: str,
    salary_range: tuple,
    include_unknown_salary: bool,
    search_keyword: str,
) -> List[Dict[str, Any]]:
    """Apply client-side filtering on the fetched dataset."""
    filtered = []
    kw = (search_keyword or "").strip().lower()

    for j in jobs:
        # 1. Search keyword (matches title, company, or skills)
        if kw:
            title_text = j.get("title", "").lower()
            company_text = j.get("company", "").lower()
            skills_text = " ".join([s.lower() for s in j.get("skills", [])])
            if kw not in title_text and kw not in company_text and kw not in skills_text:
                continue

        # 2. Job Type filter
        if selected_job_types:
            jt = j.get("employment_type", "Not provided")
            # If not matching any checked type
            if not any(t.lower() in jt.lower() for t in selected_job_types):
                continue

        # 3. Work Model filter
        if selected_work_models:
            wm = j.get("work_model", "Unknown")
            matched_wm = False
            for selected_wm in selected_work_models:
                if selected_wm.lower() in wm.lower():
                    matched_wm = True
                    break
            if not matched_wm:
                continue

        # 4. Experience Level
        if selected_exp and selected_exp != "All Levels":
            j_exp = j.get("experience_level", "Not provided")
            if j_exp != "Not provided" and selected_exp.lower() not in j_exp.lower():
                continue

        # 5. Salary Range filter
        min_filter, max_filter = salary_range
        j_min = j.get("salary_min")
        j_max = j.get("salary_max")
        if j_min is None and j_max is None:
            if not include_unknown_salary:
                continue
        else:
            effective_sal = j_max if j_max is not None else j_min
            # Only compare if currency is USD or normalized
            curr = j.get("salary_currency", "USD")
            if curr == "USD":
                if effective_sal < min_filter or effective_sal > max_filter:
                    continue

        filtered.append(j)

    return filtered


def render_job_details_dialog(job: Dict[str, Any]):
    """Render full job details in a modal or container."""
    title = job.get("title", "Job Details")
    company = job.get("company", "Company")
    location = job.get("location", "Not specified")
    work_model = job.get("work_model", "Unknown")
    emp_type = job.get("employment_type", "Not provided")
    salary_raw = job.get("salary_raw", "Not provided")
    provider = job.get("provider", "arbeitnow")
    app_url = job.get("application_url", "")
    skills = job.get("skills", [])
    desc_html = job.get("description", "")

    st.markdown(f"### {title}")
    st.markdown(f"**Company:** {company} &nbsp;|&nbsp; **Location:** 📍 {location} &nbsp;|&nbsp; **Model:** {work_model}")
    st.markdown(f"**Employment Type:** {emp_type} &nbsp;|&nbsp; **Salary:** {salary_raw} &nbsp;|&nbsp; **Source:** {provider.upper()}")

    st.markdown("#### Required / Extracted Skills")
    if skills:
        pill_html = " ".join([f'<span class="skill-pill">{html.escape(s)}</span>' for s in skills])
        st.markdown(pill_html, unsafe_allow_html=True)
    else:
        st.write("No specific skills extracted.")

    st.markdown("---")
    st.markdown("#### Full Job Description")
    # Sanitize and render
    if "<p>" in desc_html or "<div>" in desc_html:
        st.markdown(desc_html, unsafe_allow_html=True)
    else:
        st.write(job.get("plain_description") or desc_html or "No description provided.")

    st.markdown("---")
    c_apply, c_close = st.columns([2, 1])
    with c_apply:
        if app_url:
            st.markdown(f'<a href="{html.escape(app_url)}" target="_blank" style="display: inline-block; background-color: #6C47FF; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600;">Apply on Official Site ↗</a>', unsafe_allow_html=True)
        else:
            st.write("Application link not provided by source.")
    with c_close:
        if st.button("Close Details", key="btn_close_modal"):
            st.session_state["active_detail_job"] = None
            st.rerun()


def render_search_page(profile: Dict[str, Any], raw_jobs: List[Dict[str, Any]], is_demo_mode: bool):
    """Render the full Search Jobs page."""
    render_hero_banner()

    # Visibly indicate Demo Mode if active
    if is_demo_mode:
        st.markdown("""
        <div class="demo-data-banner">
            <span>✨ <b>DEMO DATA MODE:</b> Showing curated benchmark jobs matching the visual screenshot reference (Google, Microsoft, Amazon in Bengaluru). Switch off demo mode in the sidebar to fetch live listings from Arbeitnow API.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("🌐 **LIVE API MODE:** Fetching live public tech jobs from Arbeitnow API (primarily EU & Global Remote positions).")

    # Handle Active Detail Job Modal
    if st.session_state.get("active_detail_job"):
        with st.container():
            render_job_details_dialog(st.session_state["active_detail_job"])
            return

    # Popular skills chip options
    popular_skills = [
        "Python", "Data Analyst", "Machine Learning", "AI",
        "Cloud", "SQL", "Power BI", "NLP", "Backend", "Frontend"
    ]

    # Initialize search state defaults from profile if not set
    if "search_query" not in st.session_state:
        st.session_state["search_query"] = "Data Scientist" if is_demo_mode else (profile.get("skills", [""])[0] if profile.get("skills") else "Python")
    if "search_location" not in st.session_state:
        st.session_state["search_location"] = "Bengaluru, India" if is_demo_mode else profile.get("preferred_location", "")
    if "search_work_model" not in st.session_state:
        st.session_state["search_work_model"] = "All"

    # Search Panel Card
    with st.container():
        st.markdown('<div class="search-panel-card">', unsafe_allow_html=True)
        c_q, c_loc, c_wm, c_btn = st.columns([4, 3, 2, 2])

        with c_q:
            query_input = st.text_input(
                "Job Title / Skills",
                value=st.session_state["search_query"],
                placeholder="e.g. Data Scientist, Python, ML",
                key="input_search_query"
            )

        with c_loc:
            loc_input = st.text_input(
                "Location",
                value=st.session_state["search_location"],
                placeholder="e.g. Bengaluru, India or Remote",
                key="input_search_loc"
            )

        with c_wm:
            wm_options = ["All", "Remote", "Hybrid", "On-site"]
            current_wm_idx = wm_options.index(st.session_state["search_work_model"]) if st.session_state["search_work_model"] in wm_options else 0
            wm_select = st.selectbox(
                "Work Model",
                options=wm_options,
                index=current_wm_idx,
                key="select_work_model"
            )

        with c_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            search_clicked = st.button("🔍 Search Jobs", type="primary", use_container_width=True)

        # Popular Skill Chips row using native st.pills for clean wrapped labels
        selected_pill = st.pills(
            "Popular Skills:",
            options=popular_skills,
            selection_mode="single",
            key="pills_popular_skills_select"
        )
        if selected_pill and selected_pill != st.session_state.get("last_clicked_pill"):
            st.session_state["last_clicked_pill"] = selected_pill
            current_parts = [p.strip() for p in query_input.split(",") if p.strip()]
            if selected_pill not in current_parts:
                current_parts.append(selected_pill)
            st.session_state["search_query"] = ", ".join(current_parts)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # If search button clicked, update state
    if search_clicked:
        st.session_state["search_query"] = query_input
        st.session_state["search_location"] = loc_input
        st.session_state["search_work_model"] = wm_select
        st.session_state["page_number"] = 1

    active_query = st.session_state["search_query"]
    active_loc = st.session_state["search_location"]
    active_wm = st.session_state["search_work_model"]

    # Gather Sidebar Filter values from session_state
    filter_job_types = st.session_state.get("filter_job_types", ["Full-time"])
    filter_work_models = st.session_state.get("filter_work_models", ["Remote"] if not is_demo_mode else ["Remote", "Hybrid", "On-site"])
    filter_exp = st.session_state.get("filter_exp", "All Levels")
    filter_salary = st.session_state.get("filter_salary", (0, 300000))
    filter_include_unknown = st.session_state.get("filter_include_unknown_salary", True)
    filter_sort = st.session_state.get("filter_sort", "Relevance")

    # If user picked a specific work model in search panel, add it to filter
    if active_wm != "All" and active_wm not in filter_work_models:
        filter_work_models = [active_wm]

    # 1. Apply Local Filters
    filtered_jobs = apply_local_filters(
        jobs=raw_jobs,
        selected_job_types=filter_job_types,
        selected_work_models=filter_work_models,
        selected_exp=filter_exp,
        salary_range=filter_salary,
        include_unknown_salary=filter_include_unknown,
        search_keyword="",
    )

    # 2. Apply Explainable Ranking (70% Skills + 30% Location)
    ranked_jobs = rank_jobs(
        jobs=filtered_jobs,
        requested_skills_str=active_query,
        preferred_location_str=active_loc,
        sort_by=filter_sort,
    )

    # 3. Upsert into MySQL and save Search Transaction
    profile_id = profile.get("id", 1)
    if search_clicked or st.session_state.get("record_search_needed", False):
        try:
            # Upsert jobs to DB
            upsert_jobs_and_skills(raw_jobs)
            # Save search record
            save_search_transaction(
                profile_id=profile_id,
                query=active_query,
                requested_skills=active_query,
                location=active_loc,
                filters={
                    "job_types": filter_job_types,
                    "work_models": filter_work_models,
                    "experience": filter_exp,
                    "salary": filter_salary,
                    "sort": filter_sort,
                    "demo_mode": is_demo_mode
                },
                result_count=len(ranked_jobs),
                ranked_jobs=ranked_jobs,
            )
            st.session_state["record_search_needed"] = False
        except Exception as e:
            st.warning(f"Note: Search recorded locally. Database transaction notice: {e}")

    # Layout: Central Results Area (col_left) and Right Insights Column (col_right)
    col_results, col_insights = st.columns([8, 4])

    try:
        saved_job_ids = get_saved_job_ids(profile_id=profile_id)
    except Exception:
        saved_job_ids = st.session_state.get("local_saved_ids", set())

    with col_results:
        # Results Header Row
        c_count, c_sort = st.columns([3, 2])
        with c_count:
            st.markdown(
                f'<h2 style="font-size: 20px; font-weight: 800; color: #0F172A; margin: 8px 0;">'
                f'🔍 <span style="color: #6C47FF;">{len(ranked_jobs)}</span> Jobs Found'
                f'</h2>',
                unsafe_allow_html=True
            )
        with c_sort:
            st.write(f"**Sort:** `{filter_sort}`")

        # Explain empty results honestly if 0
        if not ranked_jobs:
            st.warning(
                f"No matching jobs found in current dataset ({len(raw_jobs)} listings inspected).\n\n"
                f"- If searching for Indian cities in Live API mode: Arbeitnow predominantly indexes European and global remote listings. Try searching 'Berlin', 'Germany', or 'Remote'.\n"
                f"- Alternatively, toggle **Demo Mode** in the sidebar to explore the curated Bengaluru benchmark dataset."
            )
        else:
            # Pagination
            page_size = 5
            total_pages = max(1, (len(ranked_jobs) + page_size - 1) // page_size)
            current_page = st.session_state.get("page_number", 1)
            if current_page > total_pages:
                current_page = 1

            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(ranked_jobs))

            page_jobs = ranked_jobs[start_idx:end_idx]

            # Render Job Cards
            for idx, j in enumerate(page_jobs):
                j_id = j.get("id") or (start_idx + idx + 1)
                is_saved = j_id in saved_job_ids or str(j.get("external_id", "")) in [str(x) for x in saved_job_ids]

                def make_toggle_handler(target_job, target_id):
                    def handler(_):
                        try:
                            upsert_jobs_and_skills([target_job])
                            toggle_saved_job(profile_id=profile_id, job_id=target_id)
                        except Exception:
                            # Fallback to local session storage when database is offline
                            local_saved = st.session_state.setdefault("local_saved_ids", set())
                            if target_id in local_saved:
                                local_saved.remove(target_id)
                            else:
                                local_saved.add(target_id)
                        st.rerun()
                    return handler

                def make_details_handler(target_job):
                    def handler(_):
                        st.session_state["active_detail_job"] = target_job
                        st.rerun()
                    return handler

                render_job_card(
                    job=j,
                    is_saved=is_saved,
                    requested_skills=normalize_skill_query(active_query),
                    on_toggle_save=make_toggle_handler(j, j_id),
                    on_view_details=make_details_handler(j),
                    card_index=start_idx + idx
                )

            # Pagination Controls
            if total_pages > 1:
                st.markdown("<br/>", unsafe_allow_html=True)
                p_prev, p_info, p_next = st.columns([2, 4, 2])
                with p_prev:
                    if st.button("⬅️ Previous", disabled=(current_page <= 1), key="btn_prev_page"):
                        st.session_state["page_number"] = current_page - 1
                        st.rerun()
                with p_info:
                    st.markdown(
                        f"<div style='text-align: center; font-size: 13.5px; font-weight: 600; color: #64748B; padding-top: 6px;'>"
                        f"Page {current_page} of {total_pages} (Showing {start_idx + 1}–{end_idx} of {len(ranked_jobs)})"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with p_next:
                    if st.button("Next ➡️", disabled=(current_page >= total_pages), key="btn_next_page"):
                        st.session_state["page_number"] = current_page + 1
                        st.rerun()

    with col_insights:
        # 1. Top Recommended Skills
        render_top_skills_chart(ranked_jobs if ranked_jobs else raw_jobs)

        # 2. Job Type Distribution Donut
        render_job_type_donut(ranked_jobs if ranked_jobs else raw_jobs)

        # 3. Recent Searches Widget
        try:
            recent_list = get_recent_searches(profile_id=profile_id, limit=4)
        except Exception:
            recent_list = []

        def handle_select_search(s):
            st.session_state["search_query"] = s.get("query") or ""
            st.session_state["search_location"] = s.get("location") or ""
            st.session_state["page_number"] = 1
            st.rerun()

        def handle_view_all():
            st.session_state["current_page"] = "My Searches"
            st.rerun()

        render_recent_searches_widget(
            recent_searches=recent_list,
            on_select_search=handle_select_search,
            on_view_all=handle_view_all
        )
