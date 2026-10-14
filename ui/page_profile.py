"""Profile page module.
Allows viewing and editing candidate skills, preferred location, and preferred work model,
persisting updates to MySQL and applying them as search defaults.
"""

import streamlit as st
from database.repository import get_profile, update_profile


def render_profile_page(profile_id: int = 1):
    st.markdown('<h1 style="color: #1E1B4B; font-size: 26px; font-weight: 800; margin-bottom: 8px;">👤 Candidate Profile & Preferences</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 14px; margin-bottom: 24px;">Manage your profile and search defaults. These preferences are used automatically to rank jobs and prefill search inputs.</p>', unsafe_allow_html=True)

    db_connected = True
    try:
        prof = get_profile(profile_id=profile_id)
    except Exception as e:
        db_connected = False
        st.warning(
            f"⚠️ **MySQL Database Disconnected:**\n\n"
            f"Could not connect to MySQL server (`{e}`).\n\n"
            f"- If using **Aiven Cloud**: Free services are automatically powered off after inactivity. "
            f"Please log in to [console.aiven.io](https://console.aiven.io) and ensure your service status is **Running / Powered On**.\n"
            f"- If your Aiven service domain changed or expired, update `DB_HOST`, `DB_PORT`, and `DB_PASSWORD` in your Streamlit Cloud **App Settings → Secrets**.\n\n"
            f"*Using local session preferences in the meantime:*",
            icon="⚠️"
        )
        # Fallback profile from session state or default
        prof = st.session_state.get("profile_data", {
            "id": profile_id,
            "candidate_name": "Sindhu Suraj",
            "skills": ["Python", "Machine Learning", "SQL", "Data Analysis"],
            "preferred_location": "Bengaluru, India",
            "preferred_work_model": "All",
        })

    skills_list = prof.get("skills", [])
    skills_str = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)

    with st.form("form_edit_profile"):
        name_val = st.text_input("Candidate Full Name", value=prof.get("candidate_name", "Sindhu Suraj"))
        skills_val = st.text_area(
            "Primary Skills (Comma-separated)",
            value=skills_str,
            help="Enter your canonical skills, e.g.: Python, Machine Learning, SQL, BigQuery, Docker"
        )
        c_loc, c_wm = st.columns(2)
        with c_loc:
            loc_val = st.text_input("Preferred Location", value=prof.get("preferred_location", "Bengaluru, India"))
        with c_wm:
            wm_options = ["All", "Remote", "Hybrid", "On-site"]
            current_wm = prof.get("preferred_work_model", "All")
            idx = wm_options.index(current_wm) if current_wm in wm_options else 0
            wm_val = st.selectbox("Preferred Work Model", options=wm_options, index=idx)

        submitted = st.form_submit_button("💾 Save Profile Changes", type="primary")

        if submitted:
            # Always save to session state for immediate search usage
            st.session_state["profile_data"] = {
                "id": profile_id,
                "candidate_name": name_val,
                "skills": [s.strip() for s in skills_val.split(",") if s.strip()],
                "preferred_location": loc_val,
                "preferred_work_model": wm_val,
            }
            st.session_state["search_query"] = skills_val.split(",")[0].strip() if skills_val else ""
            st.session_state["search_location"] = loc_val
            st.session_state["search_work_model"] = wm_val

            if db_connected:
                try:
                    update_profile(
                        profile_id=profile_id,
                        candidate_name=name_val,
                        skills=skills_val,
                        preferred_location=loc_val,
                        preferred_work_model=wm_val,
                    )
                    st.success("Profile saved successfully to MySQL database!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to persist to MySQL: {e}. Saved to session state.")
            else:
                st.info("Saved to session preferences (will sync to MySQL once database is online).")
                st.rerun()
