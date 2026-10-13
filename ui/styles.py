"""Custom CSS styles implementing the dashboard visual theme matching the screenshot.
Pale blue-white background, white cards, #6C47FF purple accents, rounded pill badges,
and clean modern typography.
"""

def get_custom_css() -> str:
    return """
<style>
/* -------------------------------------------------------------
   Global Theme Overrides & Fonts
   ------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1E293B;
    background-color: #F8FAFC !important;
}

/* Streamlit Header & Footer removal */
header[data-testid="stHeader"] {
    background-color: transparent !important;
    z-index: 10;
}
footer {visibility: hidden !important;}

/* Clean up main padding */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1350px !important;
}

/* -------------------------------------------------------------
   Sidebar Styling
   ------------------------------------------------------------- */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.02) !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
}

.sidebar-brand-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 4px 18px 4px;
    margin-bottom: 12px;
    border-bottom: 1px solid #F1F5F9;
}

.sidebar-brand-icon {
    width: 36px;
    height: 36px;
    background: #6C47FF;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    font-size: 18px;
    box-shadow: 0 4px 10px rgba(108, 71, 255, 0.25);
}

.sidebar-brand-title {
    font-size: 16px;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.25;
}

.sidebar-nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 14.5px;
    font-weight: 600;
    color: #475569;
    text-decoration: none;
    margin-bottom: 4px;
    transition: all 0.15s ease-in-out;
}

.sidebar-nav-item:hover {
    background-color: #F8FAFC;
    color: #6C47FF;
}

.sidebar-nav-item.active {
    background-color: #EDE9FE !important;
    color: #6C47FF !important;
    border-left: 4px solid #6C47FF;
    padding-left: 10px;
}

.sidebar-filter-heading {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14.5px;
    font-weight: 700;
    color: #1E293B;
    margin-top: 20px;
    margin-bottom: 12px;
    padding-top: 16px;
    border-top: 1px solid #E2E8F0;
}

/* -------------------------------------------------------------
   Hero Banner Component
   ------------------------------------------------------------- */
.hero-banner-container {
    background: linear-gradient(135deg, #F3F0FF 0%, #E0F2FE 100%);
    border-radius: 16px;
    padding: 24px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 10px rgba(108, 71, 255, 0.04);
}

.hero-banner-text {
    flex: 1;
    max-width: 650px;
}

.hero-banner-heading {
    font-size: 32px;
    font-weight: 800;
    color: #1E1B4B;
    margin: 0 0 8px 0;
    letter-spacing: -0.5px;
}

.hero-banner-subtitle {
    font-size: 14.5px;
    color: #475569;
    margin: 0;
    line-height: 1.5;
    font-weight: 450;
}

/* -------------------------------------------------------------
   Search Panel Card
   ------------------------------------------------------------- */
.search-panel-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px 24px 16px 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.popular-skills-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid #F1F5F9;
}

.popular-skills-label {
    font-size: 12.5px;
    font-weight: 600;
    color: #64748B;
    margin-right: 4px;
}

/* -------------------------------------------------------------
   Job Result Cards
   ------------------------------------------------------------- */
.job-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.job-card:hover {
    border-color: #CBD5E1;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05);
}

.job-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}

.job-card-left {
    display: flex;
    gap: 16px;
    align-items: flex-start;
}

.company-avatar {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    font-size: 20px;
    font-weight: 700;
    color: #334155;
    flex-shrink: 0;
    overflow: hidden;
}

.company-avatar img {
    max-width: 34px;
    max-height: 34px;
    object-fit: contain;
}

.job-title-text {
    font-size: 17px;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 4px 0;
}

.company-meta-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 13px;
    color: #64748B;
}

.company-name {
    font-weight: 600;
    color: #334155;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.meta-bullet {
    color: #CBD5E1;
}

/* Work Model Badges */
.badge-work-model {
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    display: inline-block;
    white-space: nowrap;
}

.badge-remote {
    background-color: #DCFCE7;
    color: #166534;
    border: 1px solid #BBF7D0;
}

.badge-remote-hybrid {
    background-color: #D1FAE5;
    color: #065F46;
    border: 1px solid #A7F3D0;
}

.badge-hybrid {
    background-color: #E0F2FE;
    color: #0369A1;
    border: 1px solid #BAE6FD;
}

.badge-onsite {
    background-color: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
}

.badge-unknown {
    background-color: #F1F5F9;
    color: #64748B;
    border: 1px solid #E2E8F0;
}

/* Skill Tags Pill */
.skill-pill {
    display: inline-block;
    background-color: #EFF6FF;
    color: #2563EB;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 14px;
    margin-right: 6px;
    margin-bottom: 6px;
    border: 1px solid #DBEAFE;
}

.skill-pill.matched {
    background-color: #EDE9FE;
    color: #6C47FF;
    border: 1px solid #DDD6FE;
    font-weight: 700;
}

/* Card Description */
.job-snippet {
    font-size: 13.5px;
    color: #475569;
    line-height: 1.45;
    margin: 10px 0 14px 0;
}

/* Card Footer */
.job-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 12px;
    border-top: 1px solid #F1F5F9;
}

.relevance-box {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
}

.relevance-score-badge {
    background-color: #F5F3FF;
    color: #6C47FF;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid #DDD6FE;
}

.relevance-text {
    color: #64748B;
    font-size: 12px;
}

/* -------------------------------------------------------------
   Right Insights Column Cards
   ------------------------------------------------------------- */
.insights-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.insights-card-title {
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 14px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Skill Progress Bars */
.skill-bar-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 12.5px;
}

.skill-bar-label {
    font-weight: 600;
    color: #334155;
    width: 105px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.skill-bar-track {
    flex: 1;
    height: 8px;
    background-color: #F1F5F9;
    border-radius: 4px;
    margin: 0 10px;
    overflow: hidden;
}

.skill-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.skill-bar-percent {
    font-weight: 700;
    color: #64748B;
    font-size: 11.5px;
    width: 32px;
    text-align: right;
}

/* Recent Searches List */
.recent-search-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 6px;
    border-bottom: 1px solid #F8FAFC;
    font-size: 12.5px;
}

.recent-search-item:last-child {
    border-bottom: none;
}

.recent-search-query {
    color: #334155;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
}

.recent-search-time {
    color: #94A3B8;
    font-size: 11.5px;
}

/* -------------------------------------------------------------
   Streamlit Widget Tweaks for Match & Polish
   ------------------------------------------------------------- */
div.stButton > button[kind="primary"] {
    background-color: #6C47FF !important;
    border-color: #6C47FF !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 2px 6px rgba(108, 71, 255, 0.25) !important;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #5832E6 !important;
    border-color: #5832E6 !important;
}

/* Secondary outline button for View Details */
div.stButton > button[kind="secondary"] {
    border: 1px solid #E2E8F0 !important;
    color: #475569 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

div.stButton > button[kind="secondary"]:hover {
    border-color: #6C47FF !important;
    color: #6C47FF !important;
    background-color: #F5F3FF !important;
}

/* Pills buttons */
.stPill, .stChip {
    border-radius: 20px !important;
}

/* Demo Data Banner */
.demo-data-banner {
    background-color: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 10px 16px;
    color: #B45309;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
}
</style>
"""
