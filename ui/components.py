"""Reusable UI components for rendering job cards, hero banner,
dialogs, skill badges, and right-hand insights charts.
"""

import html
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import plotly.graph_objects as go
import streamlit as st


def render_hero_banner():
    """Render the top lavender-to-light-blue gradient banner with SVG illustration."""
    svg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "banner_illustration.svg")
    svg_content = ""
    if os.path.exists(svg_path):
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

    html_content = (
        f'<div class="hero-banner-container">'
        f'<div class="hero-banner-text">'
        f'<h1 class="hero-banner-heading">Find Your Next Opportunity</h1>'
        f'<p class="hero-banner-subtitle">'
        f'Search, explore and get personalized job recommendations based on your skills and preferences.'
        f'</p>'
        f'</div>'
        f'<div class="hero-banner-art">{svg_content}</div>'
        f'</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)


def get_company_avatar_html(company: str, logo_url: Optional[str] = None) -> str:
    """Generate company logo image or clean initial letter badge."""
    comp_name = company or "Company"
    if logo_url and logo_url.startswith("http"):
        return f'<div class="company-avatar"><img src="{html.escape(logo_url)}" alt="{html.escape(comp_name)}" onerror="this.style.display=\'none\';"/></div>'
    # Generate initials
    words = comp_name.split()
    initials = "".join([w[0].upper() for w in words[:2]]) if words else "C"
    # Choose soft background tint
    colors = ["#EDE9FE", "#E0F2FE", "#FEF3C7", "#DCFCE7", "#FCE7F3"]
    text_colors = ["#6C47FF", "#0284C7", "#D97706", "#16A34A", "#DB2777"]
    idx = sum(ord(c) for c in comp_name) % len(colors)
    bg = colors[idx]
    tc = text_colors[idx]
    return f'<div class="company-avatar" style="background-color: {bg}; color: {tc};">{initials}</div>'


def get_work_model_badge_html(work_model: str) -> str:
    """Return colored pill badge for work model."""
    wm = (work_model or "Unknown").strip()
    if "remote / hybrid" in wm.lower():
        cls = "badge-remote-hybrid"
        label = "Remote / Hybrid"
    elif "remote" in wm.lower():
        cls = "badge-remote"
        label = "Remote"
    elif "hybrid" in wm.lower():
        cls = "badge-hybrid"
        label = "Hybrid"
    elif "on-site" in wm.lower() or "onsite" in wm.lower():
        cls = "badge-onsite"
        label = "On-site"
    else:
        cls = "badge-unknown"
        label = wm or "Not specified"
    return f'<span class="badge-work-model {cls}">{html.escape(label)}</span>'


def format_relative_time(dt: Optional[datetime]) -> str:
    """Format datetime into friendly relative string e.g., 'Posted 2 days ago'."""
    if not dt or not isinstance(dt, datetime):
        return "Recently posted"
    diff = datetime.utcnow() - dt
    seconds = int(diff.total_seconds())
    if seconds < 3600:
        mins = max(1, seconds // 60)
        return f"Posted {mins}m ago"
    elif seconds < 86400:
        hrs = seconds // 3600
        return f"Posted {hrs}h ago"
    elif seconds < 86400 * 30:
        days = seconds // 86400
        return f"Posted {days} day{'s' if days > 1 else ''} ago"
    else:
        return dt.strftime("Posted %b %d")


def render_job_card(
    job: Dict[str, Any],
    is_saved: bool,
    requested_skills: List[str],
    on_toggle_save: Optional[Any] = None,
    on_view_details: Optional[Any] = None,
    card_index: int = 0
):
    """Render a high-fidelity job card matching the visual reference."""
    job_id = job.get("id") or job.get("db_id") or card_index
    title = html.escape(job.get("title", "Untitled Job"))
    company = html.escape(job.get("company", "Company"))
    location = html.escape(job.get("location") or "Location not specified")
    emp_type = html.escape(job.get("employment_type") or "Not provided")
    salary_raw = html.escape(job.get("salary_raw") or "Not provided")
    posted_text = format_relative_time(job.get("source_created_at") or job.get("fetched_at"))
    work_model_html = get_work_model_badge_html(job.get("work_model", "Unknown"))
    avatar_html = get_company_avatar_html(job.get("company", ""), job.get("company_logo_url"))

    # Verified badge for known demo companies or verified listings
    verified_badge = '<span style="color: #3B82F6; font-size: 13px;" title="Verified Employer">✓</span>' if job.get("is_verified") else ""

    # Snippet
    plain_desc = job.get("plain_description") or job.get("description", "")
    snippet = html.escape(plain_desc[:160] + ("..." if len(plain_desc) > 160 else ""))

    # Skills pills
    skills = job.get("skills", [])
    req_skills_lower = {s.lower() for s in requested_skills}
    skill_pills_html = ""
    for s in skills[:6]:
        is_match = s.lower() in req_skills_lower
        match_cls = " matched" if is_match else ""
        skill_pills_html += f'<span class="skill-pill{match_cls}">{html.escape(s)}</span>'
    if len(skills) > 6:
        skill_pills_html += f'<span class="skill-pill">+{len(skills) - 6} more</span>'

    # Relevance explanation
    relevance_score = job.get("relevance_score", 0.0)
    explanation = html.escape(job.get("ranking_explanation") or "Standard match")

    # Render card container
    card_html = (
        f'<div class="job-card">'
        f'<div class="job-card-header">'
        f'<div class="job-card-left">'
        f'{avatar_html}'
        f'<div>'
        f'<h3 class="job-title-text">{title}</h3>'
        f'<div class="company-meta-row">'
        f'<span class="company-name">{company} {verified_badge}</span>'
        f'<span class="meta-bullet">•</span>'
        f'<span>📍 {location}</span>'
        f'<span class="meta-bullet">•</span>'
        f'<span>💼 {emp_type}</span>'
        f'<span class="meta-bullet">•</span>'
        f'<span>💵 {salary_raw}</span>'
        f'<span class="meta-bullet">•</span>'
        f'<span>📅 {posted_text}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div>'
        f'{work_model_html}'
        f'</div>'
        f'</div>'
        f'<div style="margin: 12px 0 8px 0;">'
        f'{skill_pills_html}'
        f'</div>'
        f'<div class="job-snippet">{snippet}</div>'
        f'<div class="job-card-footer">'
        f'<div class="relevance-box">'
        f'<span class="relevance-score-badge">{relevance_score}% Match</span>'
        f'<span class="relevance-text">{explanation}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Action buttons row (Streamlit buttons for interactive save & details)
    c_space, c_save, c_view = st.columns([7, 2, 3])
    with c_save:
        save_icon = "❤️ Saved" if is_saved else "🤍 Save"
        if st.button(save_icon, key=f"btn_save_{job_id}_{card_index}"):
            if on_toggle_save:
                on_toggle_save(job)
    with c_view:
        if st.button("View Details", key=f"btn_view_{job_id}_{card_index}"):
            if on_view_details:
                on_view_details(job)


def render_top_skills_chart(jobs: List[Dict[str, Any]]):
    """Render Top Recommended Skills horizontal progress bars from active results."""
    # Count skill frequencies
    skill_counts: Dict[str, int] = {}
    total_jobs = max(1, len(jobs))
    for j in jobs:
        for s in j.get("skills", []):
            skill_counts[s] = skill_counts.get(s, 0) + 1

    # Sort descending
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    if not sorted_skills:
        # Default placeholder if dataset has no tags
        sorted_skills = [
            ("Python", int(0.82 * total_jobs)),
            ("SQL", int(0.68 * total_jobs)),
            ("Machine Learning", int(0.55 * total_jobs)),
            ("Data Analysis", int(0.50 * total_jobs)),
            ("Deep Learning", int(0.38 * total_jobs))
        ]

    colors = ["#6C47FF", "#38BDF8", "#34D399", "#FBBF24", "#F472B6"]

    bar_rows = []
    for i, (sk, count) in enumerate(sorted_skills):
        pct = min(100, int(round((count / total_jobs) * 100)))
        color = colors[i % len(colors)]
        bar_rows.append(
            f'<div class="skill-bar-row">'
            f'<span class="skill-bar-label" title="{html.escape(sk)}">{html.escape(sk)}</span>'
            f'<div class="skill-bar-track">'
            f'<div class="skill-bar-fill" style="width: {pct}%; background-color: {color};"></div>'
            f'</div>'
            f'<span class="skill-bar-percent">{pct}%</span>'
            f'</div>'
        )

    bars_html = "".join(bar_rows)
    chart_html = (
        f'<div class="insights-card">'
        f'<div class="insights-card-title"><span>📊 Top Recommended Skills</span></div>'
        f'{bars_html}'
        f'<div style="font-size: 11px; color: #94A3B8; margin-top: 8px;">* % of currently displayed jobs requiring each skill</div>'
        f'</div>'
    )
    st.markdown(chart_html, unsafe_allow_html=True)


def render_job_type_donut(jobs: List[Dict[str, Any]]):
    """Render Job Type Distribution Donut chart using Plotly."""
    counts = {}
    for j in jobs:
        jt = j.get("employment_type") or "Other"
        counts[jt] = counts.get(jt, 0) + 1

    if not counts:
        counts = {"Full-time": 62, "Part-time": 8, "Contract": 15, "Internship": 10, "Other": 5}

    labels = list(counts.keys())
    values = list(counts.values())

    palette = ["#6C47FF", "#38BDF8", "#34D399", "#FB923C", "#F472B6", "#94A3B8"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=palette),
        textinfo="percent",
        hoverinfo="label+value+percent",
    )])

    fig.update_layout(
        title=dict(text="💼 <b>Job Type Distribution</b>", font=dict(size=14, color="#0F172A")),
        margin=dict(l=10, r=10, t=35, b=10),
        height=220,
        showlegend=True,
        legend=dict(orientation="v", font=dict(size=11), x=1.05, y=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.markdown('<div class="insights-card" style="padding-bottom: 6px;">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


def render_recent_searches_widget(recent_searches: List[Dict[str, Any]], on_select_search=None, on_view_all=None):
    """Render Recent Searches sidebar/column card."""
    st.markdown('<div class="insights-card">', unsafe_allow_html=True)
    c_head, c_btn = st.columns([3, 1])
    with c_head:
        st.markdown('<div class="insights-card-title" style="margin: 0;">⏱️ Recent Searches</div>', unsafe_allow_html=True)
    with c_btn:
        if st.button("View All", key="btn_view_all_searches", type="secondary"):
            if on_view_all:
                on_view_all()

    if not recent_searches:
        st.markdown('<p style="font-size: 12.5px; color: #94A3B8; margin-top: 10px;">No recent searches recorded yet.</p>', unsafe_allow_html=True)
    else:
        for idx, s in enumerate(recent_searches[:4]):
            q_text = s.get("query") or s.get("requested_skills") or "All Jobs"
            loc = s.get("location")
            display_title = f"{q_text} – {loc}" if loc else q_text
            ts = s.get("timestamp")
            time_str = format_relative_time(ts)

            c_q, c_act = st.columns([4, 1])
            with c_q:
                item_html = (
                    f'<div class="recent-search-item">'
                    f'<span class="recent-search-query">🔍 {html.escape(display_title[:24])}</span>'
                    f'<span class="recent-search-time">{time_str}</span>'
                    f'</div>'
                )
                st.markdown(item_html, unsafe_allow_html=True)
            with c_act:
                if st.button("Re-run", key=f"btn_rerun_s_{s.get('id')}_{idx}", type="secondary"):
                    if on_select_search:
                        on_select_search(s)

    st.markdown('</div>', unsafe_allow_html=True)
