"""Analytics page module.
Visualizes database metrics, search activity over time, top required skills,
and work model distributions with Plotly charts.
"""

import html
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database.repository import get_analytics_metrics


def render_analytics_page():
    st.markdown('<h1 style="color: #1E1B4B; font-size: 26px; font-weight: 800; margin-bottom: 8px;">📈 Platform & Search Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 14px; margin-bottom: 24px;">Aggregated metrics from your MySQL persistent database and job index.</p>', unsafe_allow_html=True)

    try:
        metrics = get_analytics_metrics()
    except Exception as e:
        st.error(f"Failed to load analytics metrics from MySQL: {e}")
        return

    # Metric KPI Cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div class="insights-card" style="text-align: center; padding: 20px;">
            <div style="font-size: 13px; font-weight: 700; color: #64748B; text-transform: uppercase;">Indexed Jobs</div>
            <div style="font-size: 32px; font-weight: 800; color: #6C47FF; margin: 6px 0;">{metrics['total_jobs']}</div>
            <div style="font-size: 12px; color: #94A3B8;">Normalized & Stored in MySQL</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="insights-card" style="text-align: center; padding: 20px;">
            <div style="font-size: 13px; font-weight: 700; color: #64748B; text-transform: uppercase;">Total Searches</div>
            <div style="font-size: 32px; font-weight: 800; color: #0EA5E9; margin: 6px 0;">{metrics['total_searches']}</div>
            <div style="font-size: 12px; color: #94A3B8;">User Search Sessions Logged</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="insights-card" style="text-align: center; padding: 20px;">
            <div style="font-size: 13px; font-weight: 700; color: #64748B; text-transform: uppercase;">Saved Jobs</div>
            <div style="font-size: 32px; font-weight: 800; color: #EC4899; margin: 6px 0;">{metrics['total_saved']}</div>
            <div style="font-size: 12px; color: #94A3B8;">Active Bookmarks</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Charts Row 1: Top Skills Bar Chart & Work Model Distribution
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("### 🏆 Top In-Demand Skills")
        top_skills = metrics.get("top_skills", [])
        if top_skills:
            df_skills = pd.DataFrame(top_skills)
            fig_skills = px.bar(
                df_skills,
                x="count",
                y="skill",
                orientation="h",
                color="count",
                color_continuous_scale=["#C7D2FE", "#6C47FF"],
                labels={"count": "Mentions in Jobs", "skill": "Skill"},
            )
            fig_skills.update_layout(
                yaxis=dict(autorange="reversed"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=320,
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_skills, use_container_width=True)
        else:
            st.info("No skill relationship data yet. Run searches to populate job skills!")

    with c_right:
        st.markdown("### 🏢 Work Model Breakdown")
        wm_data = metrics.get("work_models", {})
        if wm_data:
            fig_wm = go.Figure(data=[go.Pie(
                labels=list(wm_data.keys()),
                values=list(wm_data.values()),
                hole=0.5,
                marker=dict(colors=["#6C47FF", "#10B981", "#F59E0B", "#94A3B8"]),
            )])
            fig_wm.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_wm, use_container_width=True)
        else:
            st.info("No work model distribution data available yet.")

    # Charts Row 2: Search Activity Timeline
    st.markdown("### 📅 Search Activity Timeline")
    timeline_data = metrics.get("timeline", [])
    if timeline_data:
        df_tl = pd.DataFrame(timeline_data)
        df_tl["timestamp"] = pd.to_datetime(df_tl["timestamp"])
        df_tl = df_tl.sort_values("timestamp")
        fig_tl = px.line(
            df_tl,
            x="timestamp",
            y="count",
            markers=True,
            labels={"timestamp": "Time", "count": "Results Found"},
            line_shape="spline",
        )
        fig_tl.update_traces(line_color="#6C47FF")
        fig_tl.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("No timeline data recorded yet. Searches will automatically appear here.")
