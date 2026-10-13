-- Schema for Job Search & Recommendation App
-- Database: MySQL 8.0+

CREATE DATABASE IF NOT EXISTS job_search_rec
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE job_search_rec;

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_name VARCHAR(150) NOT NULL DEFAULT 'Candidate',
    skills TEXT NULL COMMENT 'Comma-separated canonical skills',
    preferred_location VARCHAR(150) NULL,
    preferred_work_model VARCHAR(50) NOT NULL DEFAULT 'All',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed default single-user profile if table is empty
INSERT INTO profiles (id, candidate_name, skills, preferred_location, preferred_work_model)
SELECT 1, 'Sindhu Suraj', 'Python, Machine Learning, SQL, Data Analysis', 'Bengaluru, India', 'All'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM profiles WHERE id = 1);

-- 2. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(50) NOT NULL DEFAULT 'arbeitnow',
    external_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255) NULL,
    description LONGTEXT NULL,
    application_url VARCHAR(1000) NULL,
    remote TINYINT(1) NOT NULL DEFAULT 0,
    work_model VARCHAR(50) NOT NULL DEFAULT 'Unknown' COMMENT 'Remote, Hybrid, On-site, or Unknown',
    employment_type VARCHAR(100) NULL COMMENT 'Full-time, Part-time, Contract, Internship, etc.',
    experience_level VARCHAR(50) NULL COMMENT 'Entry, Mid, Senior, Lead, or Not provided',
    salary_min DECIMAL(12,2) NULL,
    salary_max DECIMAL(12,2) NULL,
    salary_currency VARCHAR(10) NULL,
    salary_period VARCHAR(20) NULL COMMENT 'year, month, hour',
    salary_raw VARCHAR(255) NULL,
    company_logo_url VARCHAR(1000) NULL,
    source_created_at DATETIME NULL,
    fetched_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_provider_ext (provider, external_id),
    INDEX idx_jobs_company (company),
    INDEX idx_jobs_location (location),
    INDEX idx_jobs_work_model (work_model),
    INDEX idx_jobs_employment_type (employment_type),
    INDEX idx_jobs_fetched_at (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Skills Canonical Table
CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_skills_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Job-Skills Junction Table
CREATE TABLE IF NOT EXISTS job_skills (
    job_id INT NOT NULL,
    skill_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id, skill_id),
    INDEX idx_job_skills_skill (skill_id),
    CONSTRAINT fk_job_skills_job FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_job_skills_skill FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Searches Table
CREATE TABLE IF NOT EXISTS searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NULL,
    query VARCHAR(255) NULL,
    requested_skills TEXT NULL,
    location VARCHAR(255) NULL,
    filters JSON NULL,
    result_count INT NOT NULL DEFAULT 0,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_searches_profile (profile_id),
    INDEX idx_searches_timestamp (timestamp),
    CONSTRAINT fk_searches_profile FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Search Results Junction Table
CREATE TABLE IF NOT EXISTS search_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    search_id INT NOT NULL,
    job_id INT NOT NULL,
    relevance_score FLOAT NOT NULL,
    ranking_explanation TEXT NULL,
    INDEX idx_results_search (search_id),
    INDEX idx_results_job (job_id),
    CONSTRAINT fk_results_search FOREIGN KEY (search_id) REFERENCES searches (id) ON DELETE CASCADE,
    CONSTRAINT fk_results_job FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Saved Jobs Table
CREATE TABLE IF NOT EXISTS saved_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NOT NULL,
    job_id INT NOT NULL,
    saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_profile_job (profile_id, job_id),
    INDEX idx_saved_profile (profile_id),
    INDEX idx_saved_job (job_id),
    CONSTRAINT fk_saved_profile FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE,
    CONSTRAINT fk_saved_job FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
