"""About page module.
Documents the architecture, Arbeitnow API provider attribution,
ranking algorithm formulas, and honest data handling policies.
"""

import streamlit as st


def render_about_page():
    st.markdown('<h1 style="color: #1E1B4B; font-size: 26px; font-weight: 800; margin-bottom: 8px;">ℹ️ About Job Search & Recommendation</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 14px; margin-bottom: 24px;">Complete architectural overview, ranking methodology, and provider attribution.</p>', unsafe_allow_html=True)

    with st.expander("🏗️ 1. Architecture & Technology Stack", expanded=True):
        st.markdown("""
        - **Frontend:** Streamlit with custom CSS, responsive layout, and interactive dialogs.
        - **Backend:** Python 3.10+ modular service layer.
        - **Database:** MySQL 8.0 with SQLAlchemy ORM and PyMySQL driver, storing normalized relational tables:
          - `profiles`: Single-user candidate skills and preferences.
          - `jobs`: Provider external ID, title, company, location, work model, application URL, salary, and timestamps.
          - `skills`: Canonical skill names.
          - `job_skills`: Many-to-many junction table linking jobs and canonical skills.
          - `searches`: User search query sessions, filters, and timestamps.
          - `search_results`: Top ranked results with match scores and explanations.
          - `saved_jobs`: User bookmarked jobs with composite primary key and foreign keys.
        - **External API:** Arbeitnow public job board REST API.
        """)

    with st.expander("⚖️ 2. Explainable Recommendation & Ranking Logic", expanded=True):
        st.markdown("""
        The recommendation engine uses a deterministic, explainable scoring formula:
        $$\\text{Final Score} = (0.70 \\times \\text{Skill Match}) + (0.30 \\times \\text{Location Match})$$

        - **Normalization Rule:** If only skills are provided, Skill Match represents 100% of the score. If only location is provided, Location Match represents 100%. If neither is specified, jobs are ordered strictly by newest timestamp.
        - **Skill Matching ($0.0 - 1.0$):**
          $$\\text{Skill Match} = \\frac{\\text{Matched Requested Skills}}{\\text{Total Requested Skills}}$$
          Token-aware regular expressions ensure word boundaries (`\\b`) so that `Java` does not match `JavaScript`, and aliases such as `ML` $\\rightarrow$ `Machine Learning` are automatically resolved.
        - **Location Matching ($0.0 - 1.0$):**
          - Exact city/region match: **1.0**
          - Partial city match: **0.9**
          - Remote role when applicant accepts remote: **0.6**
          - Remote role with restricted regional eligibility (e.g. US only): **0.15**
          - No match: **0.0**
        - **Tie-Breaking:** Higher score first, then newest timestamp, then deterministic ID.
        """)

    with st.expander("🌐 3. Data Attribution & Honest Handling Policies", expanded=True):
        st.markdown("""
        - **Data Source Attribution:** Job listings in live mode are retrieved from the [Arbeitnow Job Board API](https://www.arbeitnow.com/api/job-board-api) under their terms of service.
        - **Geographic Coverage Reality:** Arbeitnow primarily indexes job positions located in Germany, Europe, and global remote vacancies. Therefore, live queries for Indian cities (such as Bengaluru) may legitimately return zero results.
        - **No Hallucinated Data:** Live jobs never invent salaries, logos, verification badges, or experience requirements. Missing data is transparently flagged as `Not provided` or `Unknown`.
        - **Demo Mode:** An explicit curated benchmark dataset is provided to allow previewing the user interface with the tech companies and Indian locations depicted in the visual benchmark. Demo data is clearly segregated and labeled.
        """)
