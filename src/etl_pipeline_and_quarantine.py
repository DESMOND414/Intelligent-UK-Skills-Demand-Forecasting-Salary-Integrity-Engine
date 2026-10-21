"""
Automated Python-to-SQL-to-Power BI Pipeline for the Intelligent UK Skills Demand
Forecasting & Salary Integrity Engine.

Pipeline Stages:
1. Standardise five mixed date formats (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-Mon-YYYY`,
   `YYYY.MM.DD`, `Mon DD, YYYY`) into ISO dates.
2. Clean '£' / 'GBP' / 'k' salary strings and enforce strict numeric data types.
3. Apply vectorised anomaly filters to quarantine impossible records (~8,420 rows):
   - Salary minimum > Salary maximum
   - Closing date < Posting date
   - Unparseable/missing salary or negative experience years
4. Standardise 20 inconsistent seniority labels and recalculate true seniority tiers
   from `experience_years` using vectorised `np.select` logic, flagging false-seniority
   labelling.
5. Engineer the **Posting Attractiveness Score (0–100)** and **Role Salary Volatility
   Index (Coefficient of Variation, CV = std / mean)**.
6. Parse raw skills into a normalised 1-to-many `posting_skills` table and load
   all tables into SQL via SQLAlchemy, then execute the correlated subquery /
   conditional aggregation SQL analytics (no CTEs or window functions).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
DB_PATH = PROC_DIR / "uk_skills_salary_engine.db"

SKILL_CATEGORIES = {
    "Python": "Programming & Scripting",
    "SQL": "Programming & Scripting",
    "Java": "Programming & Scripting",
    "PySpark": "Big Data & Lakehouse",
    "Databricks": "Big Data & Lakehouse",
    "Snowflake": "Cloud Data Warehouse",
    "Azure Synapse": "Cloud Data Warehouse",
    "dbt": "Data Transformation & ELT",
    "Airflow": "Orchestration & Pipelines",
    "Kafka": "Streaming & Event Driven",
    "SSIS": "Orchestration & Pipelines",
    "Power BI": "BI & Visualisation",
    "DAX": "BI & Visualisation",
    "Power Query": "BI & Visualisation",
    "Tableau": "BI & Visualisation",
    "Excel": "BI & Visualisation",
    "PyTorch": "Machine Learning & AI",
    "scikit-learn": "Machine Learning & AI",
    "XGBoost": "Machine Learning & AI",
    "MLflow": "Machine Learning & AI",
    "NLP": "Machine Learning & AI",
    "Statistics": "Analytics & Governance",
    "Pandas": "Programming & Scripting",
    "Azure": "Cloud & DevOps",
    "AWS": "Cloud & DevOps",
    "Terraform": "Cloud & DevOps",
    "Docker": "Cloud & DevOps",
    "Kubernetes": "Cloud & DevOps",
    "CI/CD": "Cloud & DevOps",
    "Git": "Cloud & DevOps",
    "Linux": "Cloud & DevOps",
    "Spring Boot": "Backend Engineering",
    "PostgreSQL": "Cloud Data Warehouse",
    "REST APIs": "Backend Engineering",
    "Microservices": "Backend Engineering",
    "FastAPI": "Backend Engineering",
    "Data Modelling": "Analytics & Governance",
    "Risk Modelling": "Analytics & Governance",
    "Credit Analytics": "Analytics & Governance",
    "SAS": "Analytics & Governance",
    "Data Quality": "Analytics & Governance",
    "Unity Catalog": "Analytics & Governance",
    "GDPR": "Analytics & Governance",
    "Metadata Management": "Analytics & Governance",
}

# Mapping of the 20 raw seniority labels to canonical tiers for comparison
RAW_LABEL_TO_CANONICAL = {
    "Entry-Level": "Junior", "Jr.": "Junior", "Junior": "Junior",
    "Graduate": "Junior", "Trainee / Assoc": "Junior",
    "Mid-Level": "Mid-Level", "Intermediate": "Mid-Level", "Regular": "Mid-Level",
    "Mid Tier": "Mid-Level", "Associate II": "Mid-Level",
    "Senior": "Senior", "Sr.": "Senior", "Snr": "Senior",
    "Senior-Level": "Senior", "Experienced Snr": "Senior",
    "Lead": "Lead / Principal", "Principal": "Lead / Principal", "Staff": "Lead / Principal",
    "Lead / Principal": "Lead / Principal", "Head / Director": "Lead / Principal",
}


def parse_five_mixed_date_formats(series: pd.Series) -> pd.Series:
    """Vectorised multi-format date parser handling all 5 mixed UK/ISO date formats."""
    s = series.astype(str).str.strip()
    parsed = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    for fmt in ["%d/%m/%Y", "%d-%b-%Y", "%Y.%m.%d", "%b %d, %Y"]:
        mask = parsed.isna()
        if not mask.any():
            break
        parsed.loc[mask] = pd.to_datetime(s.loc[mask], format=fmt, errors="coerce")
    return parsed


def clean_gbp_salary_strings(series: pd.Series) -> pd.Series:
    """Clean '£', 'GBP', commas, '/yr', 'p.a.' and 'k' suffixes into numeric floats."""
    s = series.astype(str).str.strip().str.lower()
    has_k = s.str.contains(r"\d+(?:\.\d+)?k\b", regex=True, na=False)

    cleaned = (
        s.str.replace("£", "", regex=False)
        .str.replace("gbp", "", regex=False)
        .str.replace("p.a.", "", regex=False)
        .str.replace("/yr", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("k", "", regex=False)
        .str.strip()
    )
    num = pd.to_numeric(cleaned, errors="coerce")
    num = np.where(has_k, num * 1000.0, num)
    return pd.Series(num, index=series.index, dtype=float)


def run_etl_pipeline() -> None:
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / "uk_job_postings_100k_raw.csv"
    df = pd.read_csv(raw_path)
    print(f"[ETL] Loaded {len(df):,} raw UK job postings")

    # 1. Standardise 5 mixed date formats
    df["posting_date_dt"] = parse_five_mixed_date_formats(df["raw_posting_date"])
    df["closing_date_dt"] = parse_five_mixed_date_formats(df["raw_closing_date"])

    # 2. Clean '£' salary strings & enforce numeric types
    df["salary_min_gbp"] = clean_gbp_salary_strings(df["raw_salary_min"])
    df["salary_max_gbp"] = clean_gbp_salary_strings(df["raw_salary_max"])
    df["experience_years"] = pd.to_numeric(df["experience_years"], errors="coerce")
    df["views_count"] = pd.to_numeric(df["views_count"], errors="coerce").fillna(0).astype(int)
    df["applications_count"] = pd.to_numeric(df["applications_count"], errors="coerce").fillna(0).astype(int)

    # 3. Anomaly Filters to Quarantine Impossible Records
    cond_unparseable = (
        df["salary_min_gbp"].isna()
        | df["salary_max_gbp"].isna()
        | df["posting_date_dt"].isna()
        | df["closing_date_dt"].isna()
        | (df["experience_years"] < 0)
    )
    cond_sal_inverted = (~cond_unparseable) & (df["salary_min_gbp"] > df["salary_max_gbp"])
    cond_date_inverted = (~cond_unparseable) & (~cond_sal_inverted) & (df["closing_date_dt"] < df["posting_date_dt"])

    is_quarantined = cond_unparseable | cond_sal_inverted | cond_date_inverted

    quarantine_df = df.loc[is_quarantined].copy()
    quarantine_df["quarantine_reason"] = np.select(
        [
            cond_sal_inverted.loc[is_quarantined],
            cond_date_inverted.loc[is_quarantined],
        ],
        [
            "Impossible Salary Band: salary_min_gbp > salary_max_gbp",
            "Impossible Timeline: closing_date < posting_date",
        ],
        default="Corrupted/Unparseable Salary or Negative Experience Years",
    )

    quarantine_export = quarantine_df[[
        "job_id", "job_title", "role_family", "region",
        "raw_posting_date", "raw_closing_date", "raw_salary_min", "raw_salary_max",
        "salary_min_gbp", "salary_max_gbp", "experience_years", "quarantine_reason"
    ]].rename(columns={
        "salary_min_gbp": "parsed_salary_min_gbp",
        "salary_max_gbp": "parsed_salary_max_gbp",
    })

    clean_df = df.loc[~is_quarantined].copy().reset_index(drop=True)
    print(f"[Quarantine] Quarantined {len(quarantine_export):,} impossible/corrupted records; retained {len(clean_df):,} valid records")

    # 4. Recalculate Seniority Tiers from Experience Years using Vectorised Logic
    exp = clean_df["experience_years"].values
    clean_df["recalculated_seniority"] = np.select(
        [exp < 2.0, exp < 5.0, exp < 8.5],
        ["Junior", "Mid-Level", "Senior"],
        default="Lead / Principal",
    )
    advertised_canonical = clean_df["raw_seniority_label"].map(RAW_LABEL_TO_CANONICAL)
    clean_df["is_false_seniority_label"] = (advertised_canonical != clean_df["recalculated_seniority"]).astype(int)

    # 5. Engineer Salary Midpoint, Spread, Role Salary Volatility Index (CV), and Posting Attractiveness Score
    clean_df["posting_date"] = clean_df["posting_date_dt"].dt.strftime("%Y-%m-%d")
    clean_df["closing_date"] = clean_df["closing_date_dt"].dt.strftime("%Y-%m-%d")
    clean_df["listing_duration_days"] = (clean_df["closing_date_dt"] - clean_df["posting_date_dt"]).dt.days

    clean_df["salary_midpoint_gbp"] = np.round((clean_df["salary_min_gbp"] + clean_df["salary_max_gbp"]) / 2.0, 2)
    clean_df["salary_spread_pct"] = np.round(
        ((clean_df["salary_max_gbp"] - clean_df["salary_min_gbp"]) / clean_df["salary_midpoint_gbp"]) * 100.0, 2
    )

    # Role Salary Volatility Index (Coefficient of Variation = std / mean within role_family + recalculated_seniority)
    grp_stats = (
        clean_df.groupby(["role_family", "recalculated_seniority"])["salary_midpoint_gbp"]
        .agg(role_mean="mean", role_std="std")
        .reset_index()
    )
    grp_stats["role_salary_volatility_cv"] = np.round(grp_stats["role_std"] / grp_stats["role_mean"], 4)
    clean_df = clean_df.merge(grp_stats, on=["role_family", "recalculated_seniority"], how="left")

    # Applicant conversion rate (%)
    clean_df["conversion_rate_pct"] = np.round(
        (clean_df["applications_count"] / clean_df["views_count"].replace(0, 1)) * 100.0, 2
    )
    clean_df["skills_count"] = clean_df["skills_raw"].str.count(",") + 1

    # Posting Attractiveness Score (0 - 100):
    # Combines: (a) salary competitiveness vs role+tier mean (40%), (b) work flexibility (25%),
    # (c) salary transparency/tight spread (20%), and (d) applicant conversion momentum (15%)
    sal_comp = np.clip((clean_df["salary_midpoint_gbp"] / clean_df["role_mean"]) * 50.0, 15.0, 100.0)
    flex_comp = np.where(
        clean_df["work_arrangement"] == "Remote", 95.0,
        np.where(clean_df["work_arrangement"] == "Hybrid", 72.0, 42.0)
    )
    transparency_comp = np.clip(100.0 - clean_df["salary_spread_pct"] * 1.8, 20.0, 100.0)
    conv_comp = np.clip(clean_df["conversion_rate_pct"] * 5.2, 10.0, 100.0)

    clean_df["posting_attractiveness_score"] = np.round(
        0.40 * sal_comp + 0.25 * flex_comp + 0.20 * transparency_comp + 0.15 * conv_comp,
        2,
    )

    clean_cols = [
        "job_id", "job_title", "role_family", "industry", "region", "city",
        "work_arrangement", "raw_seniority_label", "recalculated_seniority",
        "is_false_seniority_label", "experience_years", "posting_date",
        "closing_date", "listing_duration_days", "salary_min_gbp", "salary_max_gbp",
        "salary_midpoint_gbp", "salary_spread_pct", "role_salary_volatility_cv",
        "posting_attractiveness_score", "views_count", "applications_count",
        "conversion_rate_pct", "skills_count",
    ]
    clean_export = clean_df[clean_cols].copy()

    # 6. Parse Skills into Normalised 1-to-Many Table (`posting_skills`)
    skills_exploded = (
        clean_df[["job_id", "skills_raw"]]
        .assign(skill_name=clean_df["skills_raw"].str.split(", "))
        .explode("skill_name")
        .reset_index(drop=True)
    )
    skills_exploded["skill_category"] = skills_exploded["skill_name"].map(SKILL_CATEGORIES).fillna("General Technical")
    skills_exploded["is_core_skill"] = 1
    posting_skills_df = skills_exploded[["job_id", "skill_name", "skill_category", "is_core_skill"]]
    print(f"[Skills Parser] Extracted {len(posting_skills_df):,} normalised job-skill rows across {posting_skills_df['skill_name'].nunique()} unique skills")

    # 7. Load into SQL via SQLAlchemy & Run Advanced SQL Queries
    db_url = os.getenv("MYSQL_URL", f"sqlite:///{DB_PATH}")
    engine = create_engine(db_url)

    with engine.begin() as conn:
        clean_export.to_sql("job_postings_clean", conn, if_exists="replace", index=False)
        posting_skills_df.to_sql("posting_skills", conn, if_exists="replace", index=False)
        quarantine_export.to_sql("job_postings_quarantine", conn, if_exists="replace", index=False)

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jpc_role_sen ON job_postings_clean(role_family, recalculated_seniority);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jpc_region ON job_postings_clean(region);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jpc_false ON job_postings_clean(is_false_seniority_label);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ps_job ON posting_skills(job_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ps_skill ON posting_skills(skill_name);"))

    print(f"[SQLAlchemy] Loaded job_postings_clean, posting_skills, and job_postings_quarantine into {db_url}")

    # Execute the 4 advanced SQL queries (no CTEs, no window functions) and export results
    sql_text = (SQL_DIR / "02_advanced_sql_analytics.sql").read_text()
    queries = [q.strip() for q in sql_text.split(";") if q.strip()]
    query_names = [
        "sql_01_salary_integrity_gaps",
        "sql_02_remote_conversion_uplift",
        "sql_03_false_seniority_audit",
        "sql_04_skills_demand_benchmark",
    ]
    with engine.connect() as conn:
        for name, q in zip(query_names, queries):
            res_df = pd.read_sql_query(text(q), conn)
            res_df.to_csv(PROC_DIR / f"{name}.csv", index=False)
            print(f"[Advanced SQL] {name}.csv -> {len(res_df)} rows")

    # Export Power BI / GitHub summary CSVs and 10k sample
    clean_export.sample(10000, random_state=42).to_csv(PROC_DIR / "job_postings_clean_sample_10k.csv", index=False)
    quarantine_export.sample(2000, random_state=42).to_csv(PROC_DIR / "job_postings_quarantine_sample_2k.csv", index=False)

    quarantine_summary = (
        quarantine_export.groupby("quarantine_reason", as_index=False)
        .agg(quarantined_rows=("job_id", "count"))
    )
    quarantine_summary.to_csv(PROC_DIR / "quarantine_reason_summary.csv", index=False)

    role_volatility_summary = (
        clean_export.groupby(["role_family", "recalculated_seniority", "work_arrangement"], as_index=False)
        .agg(
            postings_count=("job_id", "count"),
            avg_salary_midpoint_gbp=("salary_midpoint_gbp", "mean"),
            avg_volatility_cv=("role_salary_volatility_cv", "mean"),
            avg_attractiveness_score=("posting_attractiveness_score", "mean"),
            avg_conversion_rate_pct=("conversion_rate_pct", "mean"),
            avg_applications=("applications_count", "mean"),
            false_seniority_count=("is_false_seniority_label", "sum"),
        )
    )
    role_volatility_summary.to_csv(PROC_DIR / "role_salary_and_remote_summary.csv", index=False)

    kpis = {
        "raw_total_rows": int(len(df)),
        "clean_analysis_ready_rows": int(len(clean_export)),
        "quarantined_rows": int(len(quarantine_export)),
        "quarantine_breakdown": dict(zip(quarantine_summary["quarantine_reason"], quarantine_summary["quarantined_rows"].astype(int))),
        "distinct_raw_seniority_labels_standardised": int(df["raw_seniority_label"].nunique()),
        "false_seniority_labels_detected": int(clean_export["is_false_seniority_label"].sum()),
        "false_seniority_rate_pct": round(float(clean_export["is_false_seniority_label"].mean() * 100.0), 2),
        "avg_uk_salary_midpoint_gbp": round(float(clean_export["salary_midpoint_gbp"].mean()), 2),
        "avg_posting_attractiveness_score": round(float(clean_export["posting_attractiveness_score"].mean()), 2),
        "avg_role_salary_volatility_cv": round(float(clean_export["role_salary_volatility_cv"].mean()), 4),
        "remote_avg_applications": round(float(clean_export.loc[clean_export["work_arrangement"] == "Remote", "applications_count"].mean()), 1),
        "onsite_avg_applications": round(float(clean_export.loc[clean_export["work_arrangement"] == "On-Site", "applications_count"].mean()), 1),
    }
    kpis["remote_applicant_uplift_pct"] = round(
        ((kpis["remote_avg_applications"] - kpis["onsite_avg_applications"]) / kpis["onsite_avg_applications"]) * 100.0,
        1,
    )
    (PROC_DIR / "engine_kpi_summary.json").write_text(json.dumps(kpis, indent=2))
    print("[Engine Summary]", json.dumps(kpis, indent=2))


if __name__ == "__main__":
    run_etl_pipeline()
