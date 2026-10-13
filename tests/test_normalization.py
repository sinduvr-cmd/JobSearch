"""Unit tests for text sanitization, token-aware skill extraction,
alias resolution, and honest work-model determination.
"""

import pytest
from services.normalizer import (
    sanitize_html_text,
    extract_skills_from_text,
    normalize_skill_query,
    determine_work_model,
)


def test_sanitize_html_text():
    raw_html = "<p>Join our team! <script>alert('hack');</script> We use <strong>Python</strong> &amp; SQL.</p>"
    cleaned = sanitize_html_text(raw_html)
    assert "<script>" not in cleaned
    assert "alert" not in cleaned
    assert "Python" in cleaned
    assert "&" in cleaned
    assert "<p>" not in cleaned  # Plain text extraction


def test_token_aware_java_vs_javascript():
    # Crucial requirement: Java should NOT match JavaScript
    text_with_js = "We are seeking a senior JavaScript developer with React expertise."
    skills = extract_skills_from_text(text_with_js)
    assert "JavaScript" in skills
    assert "Java" not in skills  # Must NOT false-positive match Java!

    text_with_java = "Looking for an enterprise Java backend developer using Spring Boot."
    skills_java = extract_skills_from_text(text_with_java)
    assert "Java" in skills_java
    assert "JavaScript" not in skills_java


def test_skill_alias_resolution():
    query = "ml, postgres, dl, k8s, py"
    normalized = normalize_skill_query(query)
    assert "Machine Learning" in normalized
    assert "PostgreSQL" in normalized
    assert "Deep Learning" in normalized
    assert "Kubernetes" in normalized
    assert "Python" in normalized


def test_determine_work_model_honest_reporting():
    # If remote is False and no explicit words, MUST report Unknown (never falsely assume On-site!)
    wm1 = determine_work_model(
        remote=False,
        title="Software Engineer",
        description="General responsibilities at headquarters.",
        location="Berlin, Germany"
    )
    assert wm1 == "Unknown"

    # Explicit on-site mention
    wm2 = determine_work_model(
        remote=False,
        title="Hardware Technician",
        description="This is an on-site role requiring physical presence in our lab.",
        location="Munich"
    )
    assert wm2 == "On-site"

    # Explicit hybrid mention
    wm3 = determine_work_model(
        remote=False,
        title="Data Analyst",
        description="We offer a flexible hybrid working schedule (2 days in office).",
        location="Bengaluru, India"
    )
    assert wm3 == "Hybrid"

    # Remote with hybrid
    wm4 = determine_work_model(
        remote=True,
        title="Senior Fullstack Dev",
        description="Remote / Hybrid flexibility available.",
        location="Remote"
    )
    assert wm4 == "Remote / Hybrid"

    # Pure Remote
    wm5 = determine_work_model(
        remote=True,
        title="Backend Engineer",
        description="100% remote anywhere in the world.",
        location="Remote"
    )
    assert wm5 == "Remote"
