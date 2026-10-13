"""Ranking and recommendation service implementing explainable relevance scoring.
70% Skill Relevance + 30% Location Relevance with deterministic rules,
normalization across supplied criteria, and stable tie-breaking.
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from services.normalizer import normalize_skill_query, SKILL_ALIASES


def calculate_location_relevance(
    job_location: Optional[str],
    job_remote: bool,
    job_title: str,
    job_desc: str,
    preferred_location: str
) -> Tuple[float, str]:
    """Calculate deterministic location match score between 0.0 and 1.0.
    Returns (score, reason).
    """
    if not preferred_location or not preferred_location.strip():
        return (0.0, "No preferred location specified")

    pref = preferred_location.strip().lower()
    pref_parts = [p.strip() for p in re.split(r"[,/]+", pref) if p.strip()]

    job_loc_str = (job_location or "").lower()
    combined_desc = f"{job_title} {job_desc}".lower()

    # If user explicitly requested "Remote"
    if pref in ["remote", "worldwide", "anywhere"]:
        if job_remote or "remote" in job_loc_str:
            return (1.0, "Remote position matches preferred Remote preference")
        return (0.1, "On-site/Hybrid role does not match Remote preference")

    # Check exact match with job location string
    if pref in job_loc_str:
        return (1.0, f"Exact location match ({preferred_location.strip()})")

    # Check city / sub-part match
    city_match = False
    for part in pref_parts:
        if part in job_loc_str:
            city_match = True
            break

    if city_match:
        return (0.9, f"City/area match ({preferred_location.strip()})")

    # If job is remote, respect stated geographic eligibility
    if job_remote:
        # Check if remote position has geographic restrictions (e.g., 'US only', 'Europe only', 'EMEA', 'Germany')
        restricted_regions = ["us only", "usa only", "uk only", "eu only", "europe only", "emea", "germany only"]
        for reg in restricted_regions:
            if reg in job_loc_str or reg in combined_desc:
                # If candidate is not in that region, do not match fully
                if not any(part in reg for part in pref_parts):
                    return (0.15, f"Remote role has geographic restriction ({reg.upper()})")

        return (0.6, "Remote position offers flexible location")

    return (0.0, "Location does not match preferred location")


def rank_and_explain_job(
    job: Dict[str, Any],
    requested_skills: List[str],
    preferred_location: str,
) -> Dict[str, Any]:
    """Calculate skill score, location score, combined score, and explanation.
    Weights: 70% skills, 30% location (normalized to 100% across supplied criteria).
    """
    job_skills: List[str] = job.get("skills", [])
    # Case-insensitive set of job skill canonical names
    job_skills_lower = {s.lower(): s for s in job_skills}

    # 1. Skill Relevance
    matched_skills: List[str] = []
    skill_score = 0.0
    has_skills_criterion = bool(requested_skills)

    if has_skills_criterion:
        for req in requested_skills:
            req_lower = req.lower()
            # Direct match
            if req_lower in job_skills_lower:
                matched_skills.append(job_skills_lower[req_lower])
            elif req_lower in SKILL_ALIASES:
                canon = SKILL_ALIASES[req_lower]
                if canon.lower() in job_skills_lower:
                    matched_skills.append(canon)

        matched_skills = list(dict.fromkeys(matched_skills))
        skill_score = len(matched_skills) / len(requested_skills) if requested_skills else 0.0

    # 2. Location Relevance
    has_location_criterion = bool(preferred_location and preferred_location.strip())
    loc_score, loc_reason = calculate_location_relevance(
        job_location=job.get("location"),
        job_remote=bool(job.get("remote")),
        job_title=job.get("title", ""),
        job_desc=job.get("description", ""),
        preferred_location=preferred_location,
    )

    # 3. Normalized Combined Score
    if has_skills_criterion and has_location_criterion:
        final_score = (0.70 * skill_score) + (0.30 * loc_score)
    elif has_skills_criterion:
        final_score = skill_score
    elif has_location_criterion:
        final_score = loc_score
    else:
        final_score = 0.0

    # Scale to percentage 0.0 - 100.0
    relevance_percentage = round(final_score * 100.0, 1)

    # 4. Human-readable explanation
    explanation_parts = []
    if has_skills_criterion:
        if matched_skills:
            matched_str = ", ".join(matched_skills[:4])
            if len(matched_skills) > 4:
                matched_str += f" +{len(matched_skills) - 4} more"
            explanation_parts.append(
                f"Matched {len(matched_skills)} of {len(requested_skills)} skills ({matched_str})"
            )
        else:
            explanation_parts.append(f"0 of {len(requested_skills)} requested skills matched")

    if has_location_criterion:
        explanation_parts.append(loc_reason)

    if not explanation_parts:
        explanation = "Sorted by newest posting"
    else:
        explanation = "; ".join(explanation_parts)

    job_result = dict(job)
    job_result["relevance_score"] = relevance_percentage
    job_result["ranking_explanation"] = explanation
    job_result["matched_skills"] = matched_skills
    return job_result


def rank_jobs(
    jobs: List[Dict[str, Any]],
    requested_skills_str: str,
    preferred_location_str: str,
    sort_by: str = "Relevance"
) -> List[Dict[str, Any]]:
    """Rank list of jobs, apply explanation, and sort with stable tie-breaking."""
    canonical_skills = normalize_skill_query(requested_skills_str)
    
    scored_jobs = [
        rank_and_explain_job(j, canonical_skills, preferred_location_str)
        for j in jobs
    ]

    # Deterministic sorting
    def sort_key(item):
        score = item.get("relevance_score", 0.0)
        # Date sorting helper
        dt = item.get("source_created_at") or item.get("fetched_at")
        ts = dt.timestamp() if isinstance(dt, datetime) else 0.0
        ext_id = str(item.get("external_id", ""))
        salary = item.get("salary_max") or item.get("salary_min") or 0.0

        if sort_by == "Relevance":
            # Higher score first, then newest timestamp, then external_id
            return (-score, -ts, ext_id)
        elif sort_by == "Newest":
            return (-ts, -score, ext_id)
        elif sort_by == "Salary (High to Low)":
            return (-salary, -score, -ts, ext_id)
        else:
            return (-score, -ts, ext_id)

    scored_jobs.sort(key=sort_key)
    return scored_jobs
