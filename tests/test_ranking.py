"""Unit tests for the explainable recommendation ranking algorithm.
Verifies 70/30 weighting, normalization across provided criteria,
deterministic location scoring, and stable tie-breaking.
"""

from datetime import datetime
from services.ranker import rank_and_explain_job, rank_jobs


def test_ranking_weights_and_normalization():
    sample_job = {
        "id": 1,
        "title": "Senior Data Scientist",
        "company": "TechCorp",
        "location": "Bengaluru, India",
        "remote": False,
        "skills": ["Python", "SQL", "Machine Learning", "BigQuery"],
        "description": "Building recommendation algorithms.",
    }

    # Case 1: Both skills and location supplied
    # Request 4 skills (Python, SQL, Machine Learning, Docker) -> matches 3/4 = 0.75 skill score
    # Location matches exactly "Bengaluru, India" -> 1.0 location score
    # Score = (0.70 * 0.75) + (0.30 * 1.0) = 0.525 + 0.30 = 0.825 -> 82.5%
    res1 = rank_and_explain_job(
        sample_job,
        requested_skills=["Python", "SQL", "Machine Learning", "Docker"],
        preferred_location="Bengaluru, India"
    )
    assert res1["relevance_score"] == 82.5
    assert "Matched 3 of 4 skills" in res1["ranking_explanation"]
    assert "Exact location match" in res1["ranking_explanation"]

    # Case 2: Only skills provided (Location blank)
    # Score should normalize to 100% based solely on skills -> 3/4 = 75.0%
    res2 = rank_and_explain_job(
        sample_job,
        requested_skills=["Python", "SQL", "Machine Learning", "Docker"],
        preferred_location=""
    )
    assert res2["relevance_score"] == 75.0
    assert "Matched 3 of 4 skills" in res2["ranking_explanation"]

    # Case 3: Only location provided (Skills blank)
    # Score should normalize to 100% based solely on location -> 1.0 = 100.0%
    res3 = rank_and_explain_job(
        sample_job,
        requested_skills=[],
        preferred_location="Bengaluru, India"
    )
    assert res3["relevance_score"] == 100.0
    assert "Exact location match" in res3["ranking_explanation"]

    # Case 4: Neither criterion provided
    res4 = rank_and_explain_job(
        sample_job,
        requested_skills=[],
        preferred_location=""
    )
    assert res4["relevance_score"] == 0.0
    assert "Sorted by newest" in res4["ranking_explanation"]


def test_remote_job_geographic_restriction():
    # A remote job with explicit 'US only' should NOT match candidate in Bengaluru
    us_remote_job = {
        "id": 2,
        "title": "Backend Engineer",
        "company": "USCo",
        "location": "Remote - US only",
        "remote": True,
        "skills": ["Python"],
        "description": "Must be authorized to work in the USA.",
    }

    res = rank_and_explain_job(
        us_remote_job,
        requested_skills=["Python"],
        preferred_location="Bengaluru, India"
    )
    # Skill match = 1.0 * 0.70 = 0.70
    # Location match = 0.15 * 0.30 = 0.045
    # Total = 0.745 -> 74.5% (not 0.88 or 1.0)
    assert res["relevance_score"] == 74.5
    assert "geographic restriction" in res["ranking_explanation"].lower()


def test_stable_tie_breaking():
    jobs = [
        {"id": 10, "external_id": "b", "skills": ["Python"], "location": "Bengaluru", "source_created_at": datetime(2026, 1, 1)},
        {"id": 20, "external_id": "a", "skills": ["Python"], "location": "Bengaluru", "source_created_at": datetime(2026, 1, 2)},
    ]
    ranked = rank_jobs(jobs, requested_skills_str="Python", preferred_location_str="Bengaluru")
    # Same relevance score, but job id 20 was created newer, so it should come first
    assert ranked[0]["id"] == 20
    assert ranked[1]["id"] == 10
