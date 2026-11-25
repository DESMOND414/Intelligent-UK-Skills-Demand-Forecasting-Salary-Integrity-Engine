# Intelligent UK Skills Demand Forecasting & Salary Integrity Engine

**Automated Python-to-SQL-to-Power BI Pipeline for 100,000 UK Job Postings**  
*Tools & Technologies:* **Python** (`Pandas`, `NumPy`, `SQLAlchemy`), **SQL** (`MySQL`), **Power BI** (`Power Query`, `DAX`)

---

## About the Project

**Intelligent UK Skills Demand Forecasting & Salary Integrity Engine** is an end-to-end data engineering, SQL analytics, and business intelligence project built to tackle real-world labour market data quality issues and deliver actionable recruitment and compensation insights across the UK tech job market.

Job board datasets are notoriously messy—mixing inconsistent date formats, unstandardised currency strings, inverted salary bands, impossible application timelines, and inflated or misleading seniority titles. This project automates the full ingestion, cleansing, anomaly quarantine, and analytical modelling lifecycle, transforming raw postings into a governed SQL schema and an interactive Power BI decision engine for skills demand forecasting, pay-equity auditing, and remote-work policy simulation.

---

## Project Details

- **Domain:** UK Labour Market Analytics, Data Quality Engineering & Workforce Intelligence
- **Dataset & Pipeline Scale:**
  - **100,000** deliberately unclean UK job postings ingested across **5 mixed date formats** and **20 inconsistent seniority labels**
  - **8,420** corrupted/impossible records (**8.42%**) automatically isolated into `job_postings_quarantine`
  - **91,580** clean, analysis-ready postings (**91.58%**) loaded into `job_postings_clean`
  - **412,107** normalised job-skill mappings spanning **44 unique technical skills** in `posting_skills`
- **Core Capabilities:**
  - **Automated Data Cleansing & Quarantine (Python):** Multi-pass date normalisation, `£` salary string parsing (including `k` shorthand expansion), and vectorised quarantine of inverted salary bands, impossible timelines, and invalid records.
  - **Seniority Recalculation & Integrity Auditing:** Maps 20 raw titles into 4 canonical tiers (`Junior`, `Mid-Level`, `Senior`, `Lead / Principal`) based on `experience_years`, flagging **8,326 (9.09%)** false-seniority postings and computing Role Salary Volatility ($CV$) and Posting Attractiveness Scores (0–100).
  - **Constraint-Driven SQL Analytics:** All analytical queries built using correlated subqueries, conditional aggregation, and `HAVING` clauses (strictly without CTEs or window functions).
  - **Executive BI & What-If Simulation:** Power BI model (`Power Query M` + `DAX`) featuring a dynamic **DAX Smart Narrative**, **Multi-Condition KPI Alerts**, and a **Remote Policy Adoption What-If Slider** projecting up to **+102.5% applicant uplift**.
- **Tech Stack:**
  - **Database & Querying:** MySQL / SQLAlchemy (with local SQLite mirror support)
  - **ETL & Feature Engineering:** Python (`Pandas`, `NumPy`, `SQLAlchemy`)
  - **Visualisation & BI:** Power BI (`Power Query`, `DAX`), Plotly, Matplotlib/Seaborn

---

## Executive Objective

To build an automated Python-to-SQL-to-Power BI pipeline that cleans **100,000 deliberately unclean UK job postings**, standardises **five mixed date formats** and messy **‘£’ salary strings**, quarantines **impossible records**, recalculates seniority tiers from experience years, and delivers **skills-demand forecasting**, **salary-integrity auditing**, and **remote-work applicant uplift** insights.

**Result:** Turned a deliberately unclean **100,000-row** UK job postings dataset into a **91,580-row** analysis-ready model by quarantining **8,420 corrupted records** and standardising **20 inconsistent seniority labels** into 4 canonical tiers (flagging **8,326 false-seniority postings**). Delivered a self-serve Power BI dashboard with a **DAX smart narrative**, **multi-condition KPI alerts**, and a **“Remote Policy Adoption” what-if slider** projecting up to **+102.5% applicant uplift** (+51.3% uplift at 50% adoption).

---

## Interactive Power BI Dashboard & Visual Analytics

### 1. Executive Skills Demand & Salary Integrity Engine Dashboard
![Executive Engine Dashboard](dashboard/images/executive_engine_dashboard.png)

### 2. UK Technical Skills Demand Forecasting & Salary Premium Matrix
![Skills Demand and Salary Premium](dashboard/images/skills_demand_and_salary_premium.png)

### 3. Data Integrity Quarantine Engine (~8.4k Rows) & False-Seniority Audit
![Quarantine and Seniority Audit](dashboard/images/quarantine_and_seniority_audit.png)

### 4. Power BI “Remote Policy Adoption” What-If Parameter & Applicant Uplift Simulation
![Remote Policy What-If Simulation](dashboard/images/remote_policy_whatif_simulation.png)

> **Interactive Companion Web Dashboard:** Open [`dashboard/interactive_dashboard.html`](dashboard/interactive_dashboard.html) in any browser to test the live **“Remote Policy Adoption” What-If Slider**, dynamic **DAX Smart Narrative**, and **Multi-Condition KPI Alert** banner.

---

## Pipeline Architecture & Engineering Highlights

### 1. Python Data Cleaning, Anomaly Quarantine & Feature Engineering (`src/etl_pipeline_and_quarantine.py`)
- **Five Mixed Date Formats Standardised:** Vectorised multi-pass parser converts `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-Mon-YYYY`, `YYYY.MM.DD`, and `Mon DD, YYYY` into strict ISO `DATE` columns (`posting_date`, `closing_date`).
- **‘£’ Salary String Normalisation:** Strips `£`, `GBP`, thousands commas, `/yr`, `p.a.`, and expands shorthand `k` multipliers (`£65.5k` $\rightarrow$ `65500.00`) while enforcing strict numeric types.
- **Vectorised Anomaly Quarantine (`8,420 rows isolated`):**
  - **3,650 rows** quarantined where `salary_min_gbp > salary_max_gbp` (inverted salary band).
  - **3,450 rows** quarantined where `closing_date < posting_date` (impossible timeline).
  - **1,320 rows** quarantined due to unparseable `£TBD` salary strings or negative experience years.
- **Vectorised Seniority Recalculation (`20 labels -> 4 canonical tiers`):** Consolidates 20 inconsistent raw titles (`Jr.`, `Entry-Level`, `Graduate`, `Trainee / Assoc`, `Intermediate`, `Mid Tier`, `Snr`, `Sr.`, `Staff`, `Principal`, etc.) and recalculates true seniority from `experience_years` (`Junior` <2 yrs, `Mid-Level` 2–4.9 yrs, `Senior` 5–8.4 yrs, `Lead / Principal` 8.5+ yrs), flagging **8,326 (9.09%) false-seniority postings**.
- **Engineered Metrics:**
  - **Role Salary Volatility Index ($CV = \sigma / \mu$):** Coefficient of variation of midpoint salaries within each role family and seniority tier (Market average: **0.1433**).
  - **Posting Attractiveness Score (0–100):** Weighted composite of salary competitiveness vs. role benchmark (40%), remote/hybrid flexibility (25%), salary band transparency/tightness (20%), and applicant conversion momentum (15%).

### 2. Advanced SQL Analytics — No CTEs or Window Functions (`sql/02_advanced_sql_analytics.sql`)
All analytical SQL queries are written strictly using **correlated subqueries**, **conditional aggregation (`SUM/AVG(CASE WHEN ...)` )**, and **`HAVING` clauses** without any `WITH` (CTE) or `OVER (...)` window functions:
- **Query 1 — Regional Salary Integrity Gaps:** Correlated subqueries in `SELECT` and `HAVING` detect role families and regions underpaying >10% below the UK role+seniority midpoint benchmark.
- **Query 2 — High-Conversion Postings & Remote Uplift:** Conditional aggregation compares `Remote` (15.0% conversion, 79.8 apps/posting), `Hybrid` (10.9% conversion, 58.1 apps/posting), and `On-Site` (7.5% conversion, 39.4 apps/posting).
- **Query 3 — False-Seniority Labelling Audit:** Correlated subquery compares advertised salaries on mislabelled postings against true market benchmarks.
- **Query 4 — Skills Demand & Salary Premium Benchmark:** Joins `job_postings_clean` (91,580 rows) with the normalised `posting_skills` bridge table (412,107 skill mappings across 44 technical skills).

### 3. Power BI Modelling (`powerbi/`)
- **Power Query (`M`):** [`powerbi/power_query_m.pq`](powerbi/power_query_m.pq) enforces schema types and builds custom seniority sort order columns.
- **DAX Measures:** [`powerbi/dax_measures.dax`](powerbi/dax_measures.dax) implements the **Remote Policy Adoption What-If Parameter**, **Multi-Condition Salary & Conversion Alert**, and **Executive Smart Narrative**.

---

## Key Analytical Summary

| Metric / Dimension | Result |
| :--- | :--- |
| **Raw UK Job Postings Ingested** | **100,000 rows** (5 mixed date formats, messy `£` strings, 20 seniority labels) |
| **Quarantined Impossible Records** | **8,420 rows (8.42%)** isolated into `job_postings_quarantine` |
| **Clean Analysis-Ready Postings** | **91,580 rows (91.58%)** loaded into `job_postings_clean` |
| **Normalised Job-Skill Mappings** | **412,107 rows** across **44 unique technical skills** in `posting_skills` |
| **Top In-Demand UK Tech Skills** | **Python** (45.8k postings, £70.5k avg), **SQL** (41.8k, £66.5k), **Power BI** (24.0k, £60.3k) |
| **Highest Salary Premium Skills** | **Kubernetes** (£82.7k), **XGBoost** (£78.9k), **PyTorch** (£78.8k), **Azure** (£77.1k), **Databricks** (£76.1k) |
| **What-If Remote Policy Uplift** | **+51.3% applicant uplift** at 50% adoption (**59.6 apps/post**); **+102.5%** at 100% adoption (**79.8 apps/post**) |

---

## Repository Structure

```text
uk-skills-salary-engine/
├── README.md
├── requirements.txt
├── sql/
│   ├── 01_schema_ddl.sql                      # MySQL DDL for job_postings_clean, posting_skills & job_postings_quarantine
│   └── 02_advanced_sql_analytics.sql          # Correlated subqueries, conditional aggregation & HAVING (no CTEs/window fns)
├── src/
│   ├── generate_raw_100k_postings.py          # Generates the deliberately unclean 100,000-row UK job postings dataset
│   ├── etl_pipeline_and_quarantine.py         # Cleans dates/salaries, quarantines ~8.4k rows, engineers scores & loads SQL
│   └── build_dashboard.py                     # Generates 4 high-res dashboard PNGs & interactive What-If HTML dashboard
├── powerbi/
│   ├── dax_measures.dax                       # DAX Smart Narrative, Multi-Condition Alerts & What-If Slider formulas
│   └── power_query_m.pq                       # Power Query M script for schema enforcement & seniority sorting
├── data/
│   └── processed/
│       ├── sql_01_salary_integrity_gaps.csv   # Correlated subquery output for regional salary gaps
│       ├── sql_02_remote_conversion_uplift.csv# Conditional aggregation output for remote conversion uplift
│       ├── sql_03_false_seniority_audit.csv   # False-seniority labelling audit output
│       ├── sql_04_skills_demand_benchmark.csv # Top 44 UK skills demand & salary premium output
│       ├── quarantine_reason_summary.csv      # Breakdown of the 8,420 quarantined rows
│       ├── role_salary_and_remote_summary.csv # Aggregated role, seniority & work arrangement metrics
│       ├── job_postings_clean_sample_10k.csv  # 10,000-row sample of cleaned postings for quick inspection
│       ├── job_postings_quarantine_sample_2k.csv # 2,000-row sample of quarantined anomaly records
│       └── engine_kpi_summary.json            # Full pipeline KPI metrics JSON
└── dashboard/
    ├── interactive_dashboard.html             # Self-contained HTML dashboard with live What-If Slider
    └── images/
        ├── executive_engine_dashboard.png
        ├── skills_demand_and_salary_premium.png
        ├── quarantine_and_seniority_audit.png
        └── remote_policy_whatif_simulation.png
```

---

## Quick Start & Reproducibility

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the deliberately unclean 100,000-row UK job postings dataset
python src/generate_raw_100k_postings.py

# 3. Run the Python-to-SQL ETL, anomaly quarantine (~8,420 rows), skill parsing & advanced SQL queries
# Optional: export MYSQL_URL="mysql+pymysql://user:pass@localhost:3306/uk_skills_salary_engine"
python src/etl_pipeline_and_quarantine.py

# 4. Build the dashboard images and interactive What-If HTML dashboard
python src/build_dashboard.py
```
