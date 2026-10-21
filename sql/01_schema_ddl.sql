-- =============================================================================
-- Intelligent UK Skills Demand Forecasting & Salary Integrity Engine
-- MySQL Database Schema (Clean Job Postings, Parsed Skills & Quarantine Log)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS uk_skills_salary_engine;
USE uk_skills_salary_engine;

DROP TABLE IF EXISTS posting_skills;
DROP TABLE IF EXISTS job_postings_clean;
DROP TABLE IF EXISTS job_postings_quarantine;

-- 1. Enriched & Validated UK Job Postings Table (91,600 analysis-ready records)
CREATE TABLE job_postings_clean (
    job_id VARCHAR(20) PRIMARY KEY,
    job_title VARCHAR(100) NOT NULL,
    role_family VARCHAR(60) NOT NULL,
    industry VARCHAR(60) NOT NULL,
    region VARCHAR(60) NOT NULL,
    city VARCHAR(60) NOT NULL,
    work_arrangement VARCHAR(25) NOT NULL,
    raw_seniority_label VARCHAR(40) NOT NULL,
    recalculated_seniority VARCHAR(25) NOT NULL,
    is_false_seniority_label TINYINT(1) NOT NULL DEFAULT 0,
    experience_years DECIMAL(4, 1) NOT NULL,
    posting_date DATE NOT NULL,
    closing_date DATE NOT NULL,
    listing_duration_days INT NOT NULL,
    salary_min_gbp DECIMAL(12, 2) NOT NULL,
    salary_max_gbp DECIMAL(12, 2) NOT NULL,
    salary_midpoint_gbp DECIMAL(12, 2) NOT NULL,
    salary_spread_pct DECIMAL(6, 2) NOT NULL,
    role_salary_volatility_cv DECIMAL(6, 4) NOT NULL,
    posting_attractiveness_score DECIMAL(5, 2) NOT NULL,
    views_count INT NOT NULL,
    applications_count INT NOT NULL,
    conversion_rate_pct DECIMAL(6, 2) NOT NULL,
    skills_count INT NOT NULL,
    INDEX idx_clean_role (role_family),
    INDEX idx_clean_seniority (recalculated_seniority),
    INDEX idx_clean_region (region),
    INDEX idx_clean_arrangement (work_arrangement),
    INDEX idx_clean_post_date (posting_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Parsed Job Skills Bridge Table (1-to-Many Normalized Skills Mapping)
CREATE TABLE posting_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(20) NOT NULL,
    skill_name VARCHAR(50) NOT NULL,
    skill_category VARCHAR(40) NOT NULL,
    is_core_skill TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT fk_skill_job FOREIGN KEY (job_id) REFERENCES job_postings_clean(job_id),
    INDEX idx_ps_job (job_id),
    INDEX idx_ps_skill (skill_name),
    INDEX idx_ps_category (skill_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Quarantined Anomaly Records Table (~8,400 impossible/corrupted records)
CREATE TABLE job_postings_quarantine (
    job_id VARCHAR(20) PRIMARY KEY,
    job_title VARCHAR(100),
    role_family VARCHAR(60),
    region VARCHAR(60),
    raw_posting_date VARCHAR(40),
    raw_closing_date VARCHAR(40),
    raw_salary_min VARCHAR(40),
    raw_salary_max VARCHAR(40),
    parsed_salary_min_gbp DECIMAL(12, 2),
    parsed_salary_max_gbp DECIMAL(12, 2),
    experience_years DECIMAL(5, 1),
    quarantine_reason VARCHAR(120) NOT NULL,
    INDEX idx_quar_reason (quarantine_reason)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
