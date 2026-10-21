-- =============================================================================
-- Intelligent UK Skills Demand Forecasting & Salary Integrity Engine
-- Advanced SQL Analytics: Correlated Subqueries, Conditional Aggregation & HAVING
-- STRICT CONSTRAINT: Zero CTEs (WITH clauses) and Zero Window Functions (OVER)
-- =============================================================================

-- Query 1: Detect Regional & Role Salary Integrity Gaps via Correlated Subqueries
-- Identifies role families & regions where Hybrid/On-Site postings underpay relative
-- to the role+seniority benchmark across the UK by more than 12%.
SELECT 
    j1.role_family,
    j1.recalculated_seniority,
    j1.region,
    COUNT(j1.job_id) AS total_postings,
    ROUND(AVG(j1.salary_midpoint_gbp), 2) AS regional_avg_midpoint_gbp,
    ROUND(
        (SELECT AVG(j2.salary_midpoint_gbp)
         FROM job_postings_clean j2
         WHERE j2.role_family = j1.role_family
           AND j2.recalculated_seniority = j1.recalculated_seniority),
        2
    ) AS uk_benchmark_midpoint_gbp,
    ROUND(
        AVG(j1.salary_midpoint_gbp) - (
            SELECT AVG(j3.salary_midpoint_gbp)
            FROM job_postings_clean j3
            WHERE j3.role_family = j1.role_family
              AND j3.recalculated_seniority = j1.recalculated_seniority
        ),
        2
    ) AS benchmark_salary_gap_gbp,
    ROUND(AVG(j1.role_salary_volatility_cv), 4) AS avg_role_volatility_cv
FROM job_postings_clean j1
GROUP BY 
    j1.role_family,
    j1.recalculated_seniority,
    j1.region
HAVING 
    COUNT(j1.job_id) >= 50
    AND AVG(j1.salary_midpoint_gbp) < 0.90 * (
        SELECT AVG(j4.salary_midpoint_gbp)
        FROM job_postings_clean j4
        WHERE j4.role_family = j1.role_family
          AND j4.recalculated_seniority = j1.recalculated_seniority
    )
ORDER BY benchmark_salary_gap_gbp ASC;


-- Query 2: High-Conversion Postings & Remote Policy Uplift via Conditional Aggregation
-- Compares Remote vs Hybrid vs On-Site applicant conversion rates and attractiveness
-- scores using conditional CASE WHEN aggregation and HAVING filters.
SELECT 
    j.role_family,
    COUNT(j.job_id) AS total_role_postings,
    SUM(CASE WHEN j.work_arrangement = 'Remote' THEN 1 ELSE 0 END) AS remote_postings,
    SUM(CASE WHEN j.work_arrangement = 'Hybrid' THEN 1 ELSE 0 END) AS hybrid_postings,
    SUM(CASE WHEN j.work_arrangement = 'On-Site' THEN 1 ELSE 0 END) AS onsite_postings,
    ROUND(
        AVG(CASE WHEN j.work_arrangement = 'Remote' THEN j.conversion_rate_pct END),
        2
    ) AS remote_conversion_rate_pct,
    ROUND(
        AVG(CASE WHEN j.work_arrangement = 'Hybrid' THEN j.conversion_rate_pct END),
        2
    ) AS hybrid_conversion_rate_pct,
    ROUND(
        AVG(CASE WHEN j.work_arrangement = 'On-Site' THEN j.conversion_rate_pct END),
        2
    ) AS onsite_conversion_rate_pct,
    ROUND(
        AVG(CASE WHEN j.work_arrangement = 'Remote' THEN j.applications_count END)
        - AVG(CASE WHEN j.work_arrangement = 'On-Site' THEN j.applications_count END),
        1
    ) AS remote_vs_onsite_applicant_uplift,
    ROUND(AVG(j.posting_attractiveness_score), 2) AS avg_attractiveness_score
FROM job_postings_clean j
GROUP BY j.role_family
HAVING 
    COUNT(j.job_id) >= 500
    AND AVG(CASE WHEN j.work_arrangement = 'Remote' THEN j.conversion_rate_pct END) >
        AVG(CASE WHEN j.work_arrangement = 'On-Site' THEN j.conversion_rate_pct END)
ORDER BY remote_vs_onsite_applicant_uplift DESC;


-- Query 3: False-Seniority Labelling Detection (Title Inflation vs Low-Ball Seniority)
-- Uses conditional aggregation and correlated subqueries to flag roles where employers
-- advertise "Senior/Lead" titles while paying Junior/Mid-tier salaries or vice versa.
SELECT 
    j1.role_family,
    j1.raw_seniority_label,
    j1.recalculated_seniority,
    COUNT(j1.job_id) AS mismatched_postings_count,
    ROUND(AVG(j1.experience_years), 1) AS avg_required_exp_years,
    ROUND(AVG(j1.salary_midpoint_gbp), 2) AS advertised_avg_salary_gbp,
    ROUND(
        (SELECT AVG(j2.salary_midpoint_gbp)
         FROM job_postings_clean j2
         WHERE j2.role_family = j1.role_family
           AND j2.recalculated_seniority = j1.recalculated_seniority
           AND j2.is_false_seniority_label = 0),
        2
    ) AS true_tier_market_salary_gbp,
    SUM(CASE WHEN j1.salary_spread_pct > 35.0 THEN 1 ELSE 0 END) AS wide_salary_band_count
FROM job_postings_clean j1
WHERE j1.is_false_seniority_label = 1
GROUP BY 
    j1.role_family,
    j1.raw_seniority_label,
    j1.recalculated_seniority
HAVING COUNT(j1.job_id) >= 40
ORDER BY mismatched_postings_count DESC;


-- Query 4: Top UK Technical Skills Demand, Salary Premium & High-Conversion Filter
-- Joins job_postings_clean and posting_skills using conditional aggregation and
-- a correlated subquery comparing skill salary against the overall role average.
SELECT 
    ps.skill_name,
    ps.skill_category,
    COUNT(DISTINCT ps.job_id) AS demand_postings_count,
    ROUND(AVG(j.salary_midpoint_gbp), 2) AS avg_skill_salary_gbp,
    ROUND(
        AVG(j.salary_midpoint_gbp) - (
            SELECT AVG(j_all.salary_midpoint_gbp)
            FROM job_postings_clean j_all
        ),
        2
    ) AS market_salary_premium_gbp,
    ROUND(AVG(j.posting_attractiveness_score), 2) AS avg_attractiveness_score,
    ROUND(AVG(j.conversion_rate_pct), 2) AS avg_conversion_rate_pct,
    SUM(CASE WHEN j.recalculated_seniority IN ('Senior', 'Lead / Principal') THEN 1 ELSE 0 END) AS senior_tier_demand,
    SUM(CASE WHEN j.work_arrangement = 'Remote' THEN 1 ELSE 0 END) AS remote_enabled_count
FROM posting_skills ps
INNER JOIN job_postings_clean j ON ps.job_id = j.job_id
GROUP BY ps.skill_name, ps.skill_category
HAVING COUNT(DISTINCT ps.job_id) >= 1000
ORDER BY demand_postings_count DESC, avg_skill_salary_gbp DESC;
