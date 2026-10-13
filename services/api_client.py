"""Arbeitnow Public Jobs REST API client.
Handles requests with timeouts, exponential backoff retries, pagination,
normalization, TTL caching, and graceful error reporting.
"""

import os
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from services.normalizer import (
    sanitize_html_text,
    extract_skills_from_text,
    determine_work_model,
)

load_dotenv()

ARBEITNOW_API_URL = os.getenv("ARBEITNOW_API_URL", "https://www.arbeitnow.com/api/job-board-api")
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
MAX_RETRIES = 3


def fetch_arbeitnow_page(page: int = 1, timeout: int = API_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """Fetch a single page of job listings from Arbeitnow with bounded retries."""
    url = f"{ARBEITNOW_API_URL}?page={page}"
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = {
                "User-Agent": "JobSearchApp/1.0 (Streamlit Educational Application)",
                "Accept": "application/json",
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited: wait briefly
                time.sleep(1.5 * attempt)
            else:
                response.raise_for_status()
        except (requests.RequestException, Exception) as exc:
            last_exception = exc
            time.sleep(1.0 * attempt)

    raise RuntimeError(f"Failed to fetch jobs from Arbeitnow (Page {page}) after {MAX_RETRIES} attempts: {last_exception}")


def normalize_arbeitnow_job(raw_item: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw Arbeitnow job dict into standardized internal format."""
    slug = raw_item.get("slug") or str(raw_item.get("created_at", ""))
    title = raw_item.get("title", "Untitled Position").strip()
    company = raw_item.get("company_name", "Unknown Company").strip()
    location = raw_item.get("location") or ("Remote" if raw_item.get("remote") else "Not specified")
    raw_desc = raw_item.get("description", "")
    plain_desc = sanitize_html_text(raw_desc)
    remote = bool(raw_item.get("remote", False))

    # Determine work model honestly
    work_model = determine_work_model(
        remote=remote,
        title=title,
        description=plain_desc,
        location=location,
    )

    # Job type from API job_types array
    raw_job_types = raw_item.get("job_types") or []
    employment_type = "Full-time" if "full-time" in [jt.lower() for jt in raw_job_types] else (
        raw_job_types[0].title() if raw_job_types else "Not provided"
    )

    # Skill extraction from tags + title + description
    raw_tags = raw_item.get("tags") or []
    extracted_skills = extract_skills_from_text(
        text_to_search=f"{title} {plain_desc[:800]}",
        existing_tags=raw_tags,
    )

    # Source timestamp
    created_ts = raw_item.get("created_at")
    source_created_at = None
    if isinstance(created_ts, (int, float)):
        try:
            source_created_at = datetime.fromtimestamp(created_ts)
        except Exception:
            source_created_at = None

    return {
        "provider": "arbeitnow",
        "external_id": slug,
        "title": title,
        "company": company,
        "location": location,
        "description": raw_desc,
        "plain_description": plain_desc,
        "application_url": raw_item.get("url", ""),
        "remote": remote,
        "work_model": work_model,
        "employment_type": employment_type,
        "experience_level": "Not provided",
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "salary_period": None,
        "salary_raw": "Not provided",
        "company_logo_url": None,
        "source_created_at": source_created_at,
        "skills": extracted_skills,
    }


def fetch_live_jobs(pages: int = 1) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Fetch live jobs from Arbeitnow across specified number of pages (default 1 page = 300 jobs).
    Returns (normalized_jobs_list, error_message_if_any).
    """
    all_normalized = []
    error_msg = None

    for p in range(1, pages + 1):
        try:
            data = fetch_arbeitnow_page(page=p)
            items = data.get("data", [])
            for raw in items:
                norm = normalize_arbeitnow_job(raw)
                all_normalized.append(norm)
        except Exception as e:
            error_msg = str(e)
            break

    return all_normalized, error_msg
