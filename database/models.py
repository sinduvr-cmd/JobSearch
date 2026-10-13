"""SQLAlchemy ORM models for Job Search & Recommendation system.
Normalized tables: profiles, jobs, skills, job_skills, searches, search_results, saved_jobs.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric, Float,
    DateTime, ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_name = Column(String(150), nullable=False, default="Candidate")
    skills = Column(Text, nullable=True)  # Comma-separated or JSON list of skills
    preferred_location = Column(String(150), nullable=True)
    preferred_work_model = Column(String(50), nullable=False, default="All")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    searches = relationship("Search", back_populates="profile", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="profile", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_name": self.candidate_name,
            "skills": [s.strip() for s in self.skills.split(",")] if self.skills else [],
            "preferred_location": self.preferred_location or "",
            "preferred_work_model": self.preferred_work_model or "All",
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False, default="arbeitnow")
    external_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    application_url = Column(String(1000), nullable=True)
    remote = Column(Boolean, default=False)
    work_model = Column(String(50), default="Unknown")  # Remote, Hybrid, On-site, Unknown
    employment_type = Column(String(100), nullable=True)  # Full-time, Part-time, Contract, Internship, etc.
    experience_level = Column(String(50), nullable=True)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    salary_currency = Column(String(10), nullable=True)
    salary_period = Column(String(20), nullable=True)
    salary_raw = Column(String(255), nullable=True)
    company_logo_url = Column(String(1000), nullable=True)
    source_created_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="unique_provider_ext"),
    )

    job_skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    search_results = relationship("SearchResult", back_populates="job", cascade="all, delete-orphan")
    saved_instances = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "external_id": self.external_id,
            "title": self.title,
            "company": self.company,
            "location": self.location or "Not specified",
            "description": self.description or "",
            "application_url": self.application_url or "",
            "remote": bool(self.remote),
            "work_model": self.work_model or "Unknown",
            "employment_type": self.employment_type or "Not provided",
            "experience_level": self.experience_level or "Not provided",
            "salary_min": float(self.salary_min) if self.salary_min is not None else None,
            "salary_max": float(self.salary_max) if self.salary_max is not None else None,
            "salary_currency": self.salary_currency,
            "salary_period": self.salary_period,
            "salary_raw": self.salary_raw or "Not provided",
            "company_logo_url": self.company_logo_url or "",
            "source_created_at": self.source_created_at,
            "fetched_at": self.fetched_at,
        }


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job_skills = relationship("JobSkill", back_populates="skill", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills")


class Search(Base):
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    query = Column(String(255), nullable=True)
    requested_skills = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    filters = Column(JSON, nullable=True)
    result_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profile = relationship("Profile", back_populates="searches")
    results = relationship("SearchResult", back_populates="search", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "query": self.query or "",
            "requested_skills": self.requested_skills or "",
            "location": self.location or "",
            "filters": self.filters or {},
            "result_count": self.result_count,
            "timestamp": self.timestamp,
        }


class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    relevance_score = Column(Float, nullable=False)
    ranking_explanation = Column(Text, nullable=True)

    search = relationship("Search", back_populates="results")
    job = relationship("Job", back_populates="search_results")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    saved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("profile_id", "job_id", name="unique_profile_job"),
    )

    profile = relationship("Profile", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_instances")
