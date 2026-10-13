"""Unit tests for dataset filtering logic."""

import pytest
from ui.page_search import apply_local_filters


@pytest.fixture
def sample_jobs():
    return [
        {
            "id": 1,
            "title": "Data Scientist",
            "company": "Company A",
            "employment_type": "Full-time",
            "work_model": "Remote",
            "salary_min": 100000.0,
            "salary_max": 150000.0,
            "salary_currency": "USD",
            "skills": ["Python", "SQL"]
        },
        {
            "id": 2,
            "title": "Machine Learning Intern",
            "company": "Company B",
            "employment_type": "Internship",
            "work_model": "Hybrid",
            "salary_min": None,
            "salary_max": None,
            "salary_currency": None,
            "skills": ["Python", "PyTorch"]
        },
        {
            "id": 3,
            "title": "Contract DevOps Engineer",
            "company": "Company C",
            "employment_type": "Contract",
            "work_model": "On-site",
            "salary_min": 80000.0,
            "salary_max": 90000.0,
            "salary_currency": "USD",
            "skills": ["Docker", "Kubernetes"]
        }
    ]


def test_filter_job_types(sample_jobs):
    res = apply_local_filters(
        jobs=sample_jobs,
        selected_job_types=["Full-time"],
        selected_work_models=[],
        selected_exp="All Levels",
        salary_range=(0, 300000),
        include_unknown_salary=True,
        search_keyword=""
    )
    assert len(res) == 1
    assert res[0]["id"] == 1


def test_filter_work_models(sample_jobs):
    res = apply_local_filters(
        jobs=sample_jobs,
        selected_job_types=[],
        selected_work_models=["Hybrid", "On-site"],
        selected_exp="All Levels",
        salary_range=(0, 300000),
        include_unknown_salary=True,
        search_keyword=""
    )
    assert len(res) == 2
    assert {r["id"] for r in res} == {2, 3}


def test_filter_salary_unknown_handling(sample_jobs):
    # Exclude unknown salary
    res_no_unknown = apply_local_filters(
        jobs=sample_jobs,
        selected_job_types=[],
        selected_work_models=[],
        selected_exp="All Levels",
        salary_range=(0, 300000),
        include_unknown_salary=False,
        search_keyword=""
    )
    assert len(res_no_unknown) == 2
    assert 2 not in [r["id"] for r in res_no_unknown]

    # Include unknown salary
    res_with_unknown = apply_local_filters(
        jobs=sample_jobs,
        selected_job_types=[],
        selected_work_models=[],
        selected_exp="All Levels",
        salary_range=(0, 300000),
        include_unknown_salary=True,
        search_keyword=""
    )
    assert len(res_with_unknown) == 3
