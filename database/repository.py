"""Database repository module providing CRUD operations, bulk upserts,
search tracking, profile management, and saved jobs persistence.
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.connection import session_scope
from database.models import Profile, Job, Skill, JobSkill, Search, SearchResult, SavedJob


def get_profile(profile_id: int = 1) -> Dict[str, Any]:
    """Retrieve profile by ID or create default if not found."""
    with session_scope() as session:
        prof = session.query(Profile).filter_by(id=profile_id).first()
        if not prof:
            prof = Profile(
                id=profile_id,
                candidate_name="Sindhu Suraj",
                skills="Python, Machine Learning, SQL, Data Analysis",
                preferred_location="Bengaluru, India",
                preferred_work_model="All",
            )
            session.add(prof)
            session.commit()
        return prof.to_dict()


def update_profile(
    profile_id: int,
    candidate_name: str,
    skills: str,
    preferred_location: str,
    preferred_work_model: str,
) -> Dict[str, Any]:
    """Update candidate profile."""
    with session_scope() as session:
        prof = session.query(Profile).filter_by(id=profile_id).first()
        if not prof:
            prof = Profile(id=profile_id)
            session.add(prof)
        prof.candidate_name = candidate_name.strip()
        prof.skills = skills.strip()
        prof.preferred_location = preferred_location.strip()
        prof.preferred_work_model = preferred_work_model
        prof.updated_at = datetime.now(timezone.utc)
        session.commit()
        return prof.to_dict()


def upsert_jobs_and_skills(jobs_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Upsert a list of normalized job dicts into the jobs table.
    Also syncs canonical skills into skills and job_skills tables.
    Returns mapping of external_id -> job.id in DB.
    """
    if not jobs_data:
        return {}

    with session_scope() as session:
        # 1. Collect all unique skills across all jobs
        all_skills_set = set()
        for j in jobs_data:
            for s in j.get("skills", []):
                clean_s = s.strip()
                if clean_s:
                    all_skills_set.add(clean_s)

        # 2. Upsert skills table
        skill_id_map: Dict[str, int] = {}
        if all_skills_set:
            existing_skills = session.query(Skill).filter(Skill.name.in_(list(all_skills_set))).all()
            for es in existing_skills:
                skill_id_map[es.name.lower()] = es.id

            missing_skills = [
                Skill(name=s) for s in all_skills_set if s.lower() not in skill_id_map
            ]
            if missing_skills:
                session.add_all(missing_skills)
                session.flush()
                for ms in missing_skills:
                    skill_id_map[ms.name.lower()] = ms.id

        # 3. Upsert jobs using raw MySQL ON DUPLICATE KEY UPDATE for speed & atomic safety
        ext_ids = [j["external_id"] for j in jobs_data]
        job_upsert_sql = text("""
            INSERT INTO jobs (
                provider, external_id, title, company, location, description,
                application_url, remote, work_model, employment_type, experience_level,
                salary_min, salary_max, salary_currency, salary_period, salary_raw,
                company_logo_url, source_created_at, fetched_at
            ) VALUES (
                :provider, :external_id, :title, :company, :location, :description,
                :application_url, :remote, :work_model, :employment_type, :experience_level,
                :salary_min, :salary_max, :salary_currency, :salary_period, :salary_raw,
                :company_logo_url, :source_created_at, NOW()
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                company = VALUES(company),
                location = VALUES(location),
                description = VALUES(description),
                application_url = VALUES(application_url),
                remote = VALUES(remote),
                work_model = VALUES(work_model),
                employment_type = VALUES(employment_type),
                experience_level = VALUES(experience_level),
                salary_min = VALUES(salary_min),
                salary_max = VALUES(salary_max),
                salary_currency = VALUES(salary_currency),
                salary_period = VALUES(salary_period),
                salary_raw = VALUES(salary_raw),
                company_logo_url = VALUES(company_logo_url),
                fetched_at = NOW()
        """)

        for j in jobs_data:
            session.execute(
                job_upsert_sql,
                {
                    "provider": j.get("provider", "arbeitnow"),
                    "external_id": j["external_id"],
                    "title": j["title"],
                    "company": j["company"],
                    "location": j.get("location"),
                    "description": j.get("description"),
                    "application_url": j.get("application_url"),
                    "remote": 1 if j.get("remote") else 0,
                    "work_model": j.get("work_model", "Unknown"),
                    "employment_type": j.get("employment_type"),
                    "experience_level": j.get("experience_level"),
                    "salary_min": j.get("salary_min"),
                    "salary_max": j.get("salary_max"),
                    "salary_currency": j.get("salary_currency"),
                    "salary_period": j.get("salary_period"),
                    "salary_raw": j.get("salary_raw"),
                    "company_logo_url": j.get("company_logo_url"),
                    "source_created_at": j.get("source_created_at"),
                },
            )

        # 4. Fetch job IDs
        saved_jobs = session.query(Job.id, Job.external_id).filter(Job.external_id.in_(ext_ids)).all()
        ext_to_job_id = {sj.external_id: sj.id for sj in saved_jobs}

        # 5. Populate job_skills junctions
        job_skill_links = []
        for j in jobs_data:
            job_id = ext_to_job_id.get(j["external_id"])
            if not job_id:
                continue
            for s in j.get("skills", []):
                sid = skill_id_map.get(s.strip().lower())
                if sid:
                    job_skill_links.append({"job_id": job_id, "skill_id": sid})

        if job_skill_links:
            link_sql = text("""
                INSERT IGNORE INTO job_skills (job_id, skill_id, created_at)
                VALUES (:job_id, :skill_id, NOW())
            """)
            for link in job_skill_links:
                session.execute(link_sql, link)

        session.commit()
        return ext_to_job_id


def save_search_transaction(
    profile_id: Optional[int],
    query: str,
    requested_skills: str,
    location: str,
    filters: Dict[str, Any],
    result_count: int,
    ranked_jobs: List[Dict[str, Any]],
) -> int:
    """Record a search in the searches table and persist top result rankings."""
    with session_scope() as session:
        # Create search record
        search_rec = Search(
            profile_id=profile_id,
            query=query,
            requested_skills=requested_skills,
            location=location,
            filters=filters,
            result_count=result_count,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(search_rec)
        session.flush()

        search_id = search_rec.id

        # Insert up to top 30 ranked search results
        results_to_insert = []
        for item in ranked_jobs[:30]:
            job_db_id = item.get("db_id")
            if not job_db_id and "external_id" in item:
                # Find DB job id if not attached
                db_job = session.query(Job.id).filter_by(external_id=item["external_id"]).first()
                if db_job:
                    job_db_id = db_job[0]

            if job_db_id:
                results_to_insert.append(
                    SearchResult(
                        search_id=search_id,
                        job_id=job_db_id,
                        relevance_score=item.get("relevance_score", 0.0),
                        ranking_explanation=item.get("ranking_explanation", ""),
                    )
                )

        if results_to_insert:
            session.add_all(results_to_insert)

        session.commit()
        return search_id


def get_recent_searches(profile_id: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent searches for display or replay."""
    with session_scope() as session:
        query = (
            session.query(Search)
            .order_by(Search.timestamp.desc())
            .limit(limit)
        )
        return [s.to_dict() for s in query.all()]


def get_saved_job_ids(profile_id: int = 1) -> Set[int]:
    """Get the set of job IDs saved by a profile."""
    with session_scope() as session:
        saved = session.query(SavedJob.job_id).filter_by(profile_id=profile_id).all()
        return {s[0] for s in saved}


def toggle_saved_job(profile_id: int, job_id: int) -> bool:
    """Toggle save status. Returns True if now saved, False if removed."""
    with session_scope() as session:
        existing = session.query(SavedJob).filter_by(profile_id=profile_id, job_id=job_id).first()
        if existing:
            session.delete(existing)
            session.commit()
            return False
        else:
            new_saved = SavedJob(profile_id=profile_id, job_id=job_id)
            session.add(new_saved)
            session.commit()
            return True


def get_saved_jobs_detailed(profile_id: int = 1) -> List[Dict[str, Any]]:
    """Get all saved jobs for a candidate profile with full job metadata and skills."""
    with session_scope() as session:
        saved_records = (
            session.query(SavedJob, Job)
            .join(Job, SavedJob.job_id == Job.id)
            .filter(SavedJob.profile_id == profile_id)
            .order_by(SavedJob.saved_at.desc())
            .all()
        )

        results = []
        for saved_rec, job_rec in saved_records:
            job_dict = job_rec.to_dict()
            job_dict["saved_at"] = saved_rec.saved_at
            # Fetch skills for this job
            skills = (
                session.query(Skill.name)
                .join(JobSkill, Skill.id == JobSkill.skill_id)
                .filter(JobSkill.job_id == job_rec.id)
                .all()
            )
            job_dict["skills"] = [s[0] for s in skills]
            results.append(job_dict)

        return results


def get_analytics_metrics() -> Dict[str, Any]:
    """Gather metrics for analytics page: total searches, jobs count, top skills, work models."""
    with session_scope() as session:
        total_jobs = session.query(Job).count()
        total_searches = session.query(Search).count()
        total_saved = session.query(SavedJob).count()

        # Work model distribution
        wm_rows = session.execute(
            text("SELECT work_model, COUNT(*) FROM jobs GROUP BY work_model")
        ).fetchall()
        work_models = {row[0]: row[1] for row in wm_rows}

        # Employment type distribution
        emp_rows = session.execute(
            text("SELECT employment_type, COUNT(*) FROM jobs WHERE employment_type IS NOT NULL GROUP BY employment_type")
        ).fetchall()
        employment_types = {row[0]: row[1] for row in emp_rows}

        # Top 10 skills in DB
        skill_rows = session.execute(
            text("""
                SELECT s.name, COUNT(js.job_id) as cnt
                FROM skills s
                JOIN job_skills js ON s.id = js.skill_id
                GROUP BY s.id, s.name
                ORDER BY cnt DESC
                LIMIT 10
            """)
        ).fetchall()
        top_skills = [{"skill": row[0], "count": row[1]} for row in skill_rows]

        # Recent searches timeline
        search_history = (
            session.query(Search.timestamp, Search.result_count)
            .order_by(Search.timestamp.desc())
            .limit(50)
            .all()
        )
        timeline = [{"timestamp": str(sh[0]), "count": sh[1]} for sh in search_history]

        return {
            "total_jobs": total_jobs,
            "total_searches": total_searches,
            "total_saved": total_saved,
            "work_models": work_models,
            "employment_types": employment_types,
            "top_skills": top_skills,
            "timeline": timeline,
        }
