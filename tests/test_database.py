"""Integration tests for MySQL database persistence, duplicate prevention,
and saved jobs tracking.
"""

import pytest
from database.connection import test_connection as check_mysql_connection, init_db
from database.repository import (
    get_profile,
    update_profile,
    upsert_jobs_and_skills,
    toggle_saved_job,
    get_saved_job_ids,
    save_search_transaction,
    get_recent_searches,
)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    ok, _ = check_mysql_connection()
    if not ok:
        pytest.skip("MySQL connection unavailable for database integration test.")
    init_db()


def test_db_connectivity():
    ok, msg = check_mysql_connection()
    assert ok is True
    assert "Connected" in msg


def test_profile_persistence():
    prof = get_profile(profile_id=1)
    assert prof["id"] == 1
    assert "candidate_name" in prof

    # Update profile
    updated = update_profile(
        profile_id=1,
        candidate_name="Sindhu Test",
        skills="Python, SQL, PyTorch",
        preferred_location="Bengaluru, India",
        preferred_work_model="Hybrid"
    )
    assert updated["candidate_name"] == "Sindhu Test"
    assert "PyTorch" in updated["skills"]


def test_upsert_duplicate_prevention():
    # Insert job twice with same external_id
    test_job = {
        "provider": "test_provider",
        "external_id": "unique-test-job-12345",
        "title": "Initial Title",
        "company": "Test Company",
        "location": "Berlin, Germany",
        "description": "Initial description.",
        "remote": True,
        "work_model": "Remote",
        "employment_type": "Full-time",
        "skills": ["Python", "Docker"],
    }

    # First upsert
    mapping1 = upsert_jobs_and_skills([test_job])
    job_id_1 = mapping1.get("unique-test-job-12345")
    assert job_id_1 is not None

    # Modify title and re-upsert
    test_job["title"] = "Updated Title"
    mapping2 = upsert_jobs_and_skills([test_job])
    job_id_2 = mapping2.get("unique-test-job-12345")

    # MUST map to same ID, proving duplicate was prevented and row was updated
    assert job_id_1 == job_id_2


def test_saved_job_toggle_persistence():
    # Toggle save
    test_job = {
        "provider": "test_provider",
        "external_id": "test-saved-job-9999",
        "title": "Saved Job Candidate",
        "company": "Acme",
        "skills": ["Python"],
    }
    mapping = upsert_jobs_and_skills([test_job])
    jid = mapping["test-saved-job-9999"]

    # If currently saved, clear it first
    saved_ids = get_saved_job_ids(profile_id=1)
    if jid in saved_ids:
        toggle_saved_job(profile_id=1, job_id=jid)

    # 1. Save job
    is_saved = toggle_saved_job(profile_id=1, job_id=jid)
    assert is_saved is True
    assert jid in get_saved_job_ids(profile_id=1)

    # 2. Unsave job
    is_saved_again = toggle_saved_job(profile_id=1, job_id=jid)
    assert is_saved_again is False
    assert jid not in get_saved_job_ids(profile_id=1)


def test_search_history_persistence():
    sid = save_search_transaction(
        profile_id=1,
        query="Data Scientist",
        requested_skills="Python, SQL",
        location="Bengaluru, India",
        filters={"job_type": "Full-time"},
        result_count=42,
        ranked_jobs=[],
    )
    assert sid > 0

    recent = get_recent_searches(profile_id=1, limit=5)
    assert len(recent) > 0
    assert any(s["query"] == "Data Scientist" for s in recent)
