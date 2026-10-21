"""
Generate a deliberately unclean 100,000-row UK job postings dataset containing:
1. Five mixed date formats across `posting_date` and `closing_date`:
   - Format 1: YYYY-MM-DD (e.g., "2025-05-14")
   - Format 2: DD/MM/YYYY (e.g., "14/05/2025")
   - Format 3: DD-Mon-YYYY (e.g., "14-May-2025")
   - Format 4: YYYY.MM.DD (e.g., "2025.05.14")
   - Format 5: Mon DD, YYYY (e.g., "May 14, 2025")
2. Messy '£' salary strings (e.g. "£55,000", "£65.5k", "GBP 48,000 p.a.", "£72,000.00/yr").
3. 20 inconsistent seniority labels (e.g. "Jr.", "Entry-Level", "Grad", "Mid-Level",
   "Intermediate", "Snr", "Sr.", "Principal/Lead", "Staff", etc.).
4. ~8,400 impossible/corrupted records designed to be quarantined by anomaly filters:
   - Salary Minimum > Salary Maximum (~3,650 rows)
   - Closing Date < Posting Date (~3,450 rows)
   - Missing/Corrupted Salary or Negative Experience (~1,320 rows)
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

ROLE_FAMILIES = [
    ("Data Engineer", "Technology & Data", 68000, ["Python", "SQL", "PySpark", "Databricks", "Airflow", "dbt", "Snowflake", "Azure", "Kafka"]),
    ("Data Analyst", "Technology & Data", 48000, ["SQL", "Python", "Power BI", "DAX", "Power Query", "Tableau", "Excel", "Statistics"]),
    ("Analytics Engineer", "Technology & Data", 64000, ["dbt", "Snowflake", "SQL", "Python", "Git", "Airflow", "Power BI", "Data Modelling"]),
    ("Machine Learning Engineer", "AI & Data Science", 76000, ["Python", "PyTorch", "scikit-learn", "XGBoost", "MLflow", "Docker", "Kubernetes", "FastAPI"]),
    ("Data Scientist", "AI & Data Science", 66000, ["Python", "SQL", "scikit-learn", "XGBoost", "Statistics", "PyTorch", "NLP", "Pandas"]),
    ("BI Developer", "Business Intelligence", 52000, ["Power BI", "DAX", "Power Query", "SQL", "SSIS", "Tableau", "Azure Synapse", "Excel"]),
    ("Cloud Platform Engineer", "Cloud & DevOps", 72000, ["Azure", "AWS", "Terraform", "Docker", "Kubernetes", "CI/CD", "Python", "Linux"]),
    ("Backend Software Engineer", "Software Engineering", 65000, ["Python", "Java", "Spring Boot", "SQL", "PostgreSQL", "Docker", "REST APIs", "Microservices"]),
    ("Financial Risk Analyst", "FinTech & Banking", 58000, ["SQL", "Python", "Power BI", "Excel", "Risk Modelling", "Credit Analytics", "SAS", "Statistics"]),
    ("Data Governance Specialist", "Enterprise Data", 56000, ["Data Quality", "SQL", "Unity Catalog", "GDPR", "Metadata Management", "Power BI", "Python"]),
]

UK_REGIONS = [
    ("Greater London", "London", 1.22, 0.30),
    ("North West", "Manchester", 0.96, 0.13),
    ("West Midlands", "Birmingham", 0.94, 0.10),
    ("Scotland", "Edinburgh", 1.01, 0.09),
    ("South West", "Bristol", 1.00, 0.08),
    ("Yorkshire & Humber", "Leeds", 0.93, 0.08),
    ("East of England", "Cambridge", 1.08, 0.06),
    ("South East", "Reading", 1.06, 0.06),
    ("Wales", "Cardiff", 0.89, 0.05),
    ("Northern Ireland", "Belfast", 0.88, 0.05),
]

# Exactly 20 inconsistent seniority labels found in raw job board scrapes
TWENTY_RAW_SENIORITY_LABELS = [
    # Entry / Junior variants (5)
    "Entry-Level", "Jr.", "Junior", "Graduate", "Trainee / Assoc",
    # Mid-Level variants (5)
    "Mid-Level", "Intermediate", "Regular", "Mid Tier", "Associate II",
    # Senior variants (5)
    "Senior", "Sr.", "Snr", "Senior-Level", "Experienced Snr",
    # Lead / Principal / Executive variants (5)
    "Lead", "Principal", "Staff", "Lead / Principal", "Head / Director",
]


def format_mixed_dates(dates: pd.Series, rng: np.random.Generator) -> np.ndarray:
    fmt_choice = rng.integers(0, 5, size=len(dates))
    f0 = dates.dt.strftime("%Y-%m-%d")
    f1 = dates.dt.strftime("%d/%m/%Y")
    f2 = dates.dt.strftime("%d-%b-%Y")
    f3 = dates.dt.strftime("%Y.%m.%d")
    f4 = dates.dt.strftime("%b %d, %Y")
    return np.select(
        [fmt_choice == 0, fmt_choice == 1, fmt_choice == 2, fmt_choice == 3],
        [f0, f1, f2, f3],
        default=f4,
    )


def format_messy_salaries(amounts: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    style = rng.integers(0, 4, size=len(amounts))
    rounded = np.round(amounts).astype(int)
    in_k = np.round(amounts / 1000.0, 1)

    s0 = pd.Series(rounded).map(lambda x: f"£{x:,}").values
    s1 = pd.Series(in_k).map(lambda x: f"£{x}k").values
    s2 = pd.Series(rounded).map(lambda x: f"GBP {x:,} p.a.").values
    s3 = pd.Series(rounded).map(lambda x: f"£{x:,}.00/yr").values

    return np.select([style == 0, style == 1, style == 2], [s0, s1, s2], default=s3)


def generate_unclean_100k_postings(n_rows: int = 100000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    job_ids = [f"UKJOB-{i:06d}" for i in range(1, n_rows + 1)]
    role_idx = rng.choice(len(ROLE_FAMILIES), size=n_rows, p=[0.18, 0.17, 0.09, 0.09, 0.11, 0.10, 0.08, 0.08, 0.06, 0.04])
    reg_probs = [r[3] for r in UK_REGIONS]
    reg_idx = rng.choice(len(UK_REGIONS), size=n_rows, p=reg_probs)

    role_names = [ROLE_FAMILIES[i][0] for i in role_idx]
    industries = [ROLE_FAMILIES[i][1] for i in role_idx]
    base_salaries = np.array([ROLE_FAMILIES[i][2] for i in role_idx], dtype=float)

    regions = [UK_REGIONS[i][0] for i in reg_idx]
    cities = [UK_REGIONS[i][1] for i in reg_idx]
    reg_mult = np.array([UK_REGIONS[i][2] for i in reg_idx], dtype=float)

    work_arrangements = rng.choice(
        ["Remote", "Hybrid", "On-Site"],
        size=n_rows,
        p=[0.28, 0.46, 0.26],
    )

    # Experience years (0.0 to 14.0)
    exp_tier = rng.choice([0, 1, 2, 3], size=n_rows, p=[0.22, 0.36, 0.29, 0.13])
    exp_years = np.where(
        exp_tier == 0, rng.uniform(0.0, 1.9, size=n_rows),
        np.where(exp_tier == 1, rng.uniform(2.0, 4.9, size=n_rows),
        np.where(exp_tier == 2, rng.uniform(5.0, 8.4, size=n_rows),
                 rng.uniform(8.5, 14.0, size=n_rows)))
    ).round(1)

    # Assign raw seniority label from the 20 messy labels
    # Deliberately introduce ~9% false seniority labels (e.g., calling a 1-yr role "Senior" or a 7-yr role "Jr.")
    is_mislabeled = rng.random(n_rows) < 0.092
    effective_tier = np.where(is_mislabeled, (exp_tier + rng.integers(1, 4, size=n_rows)) % 4, exp_tier)
    sub_label_idx = rng.integers(0, 5, size=n_rows)
    raw_label_indices = effective_tier * 5 + sub_label_idx
    raw_seniority_labels = [TWENTY_RAW_SENIORITY_LABELS[i] for i in raw_label_indices]

    job_titles = [f"{lbl} {role}" for lbl, role in zip(raw_seniority_labels, role_names)]

    # True salary calculation driven by role, experience tier, and regional multiplier
    tier_mult = np.where(exp_tier == 0, 0.74, np.where(exp_tier == 1, 0.98, np.where(exp_tier == 2, 1.24, 1.48)))
    true_mid = base_salaries * reg_mult * tier_mult * rng.normal(1.0, 0.08, size=n_rows)
    spread = rng.uniform(0.06, 0.16, size=n_rows)
    sal_min = np.clip(true_mid * (1.0 - spread), 22000, 165000)
    sal_max = np.clip(true_mid * (1.0 + spread), 25000, 195000)

    # Posting dates across 2025
    start_ts = pd.Timestamp("2025-01-01")
    post_offsets = rng.integers(0, 335, size=n_rows)
    duration_days = rng.integers(7, 45, size=n_rows)
    post_dates = start_ts + pd.to_timedelta(post_offsets, unit="D")
    close_dates = post_dates + pd.to_timedelta(duration_days, unit="D")

    # Views and applications (Remote & higher pay attract more views/conversions)
    base_views = rng.integers(140, 920, size=n_rows)
    conv_rate = (
        np.where(work_arrangements == "Remote", 0.145, np.where(work_arrangements == "Hybrid", 0.105, 0.072))
        * np.where(sal_min > base_salaries, 1.15, 0.92)
        * rng.uniform(0.80, 1.22, size=n_rows)
    )
    applications = np.clip(np.round(base_views * conv_rate), 4, 380).astype(int)

    # Skills string per posting (3 to 6 skills)
    skills_list = []
    for r_i in role_idx:
        pool = ROLE_FAMILIES[r_i][3]
        k = int(rng.integers(3, min(7, len(pool) + 1)))
        chosen = rng.choice(pool, size=k, replace=False)
        skills_list.append(", ".join(chosen))

    # --- INJECT DELIBERATE CORRUPTIONS (~8,420 rows total) ---
    all_indices = np.arange(n_rows)
    corrupt_indices = rng.choice(all_indices, size=8420, replace=False)
    c_sal_invert = corrupt_indices[:3650]      # Salary min > max
    c_date_invert = corrupt_indices[3650:7100] # Closing date < Posting date
    c_bad_vals = corrupt_indices[7100:]        # Missing/corrupted salary or negative experience

    # 1. Invert salary min and max
    sal_min_corrupt = sal_min.copy()
    sal_max_corrupt = sal_max.copy()
    sal_min_corrupt[c_sal_invert] = sal_max[c_sal_invert] + rng.uniform(4000, 18000, size=len(c_sal_invert))
    sal_max_corrupt[c_sal_invert] = sal_min[c_sal_invert]

    # 2. Invert closing date before posting date
    close_dates_series = pd.Series(close_dates)
    post_dates_series = pd.Series(post_dates)
    close_dates_series.iloc[c_date_invert] = (
        post_dates_series.iloc[c_date_invert] - pd.to_timedelta(rng.integers(3, 28, size=len(c_date_invert)), unit="D")
    )

    # Format dates into 5 mixed string formats and salaries into '£' strings
    raw_post_str = format_mixed_dates(post_dates_series, rng)
    raw_close_str = format_mixed_dates(close_dates_series, rng)
    raw_sal_min_str = format_messy_salaries(sal_min_corrupt, rng)
    raw_sal_max_str = format_messy_salaries(sal_max_corrupt, rng)

    # 3. Apply unparseable salary strings or negative experience on c_bad_vals
    half_bad = len(c_bad_vals) // 2
    raw_sal_min_str[c_bad_vals[:half_bad]] = "£TBD / Competitive"
    exp_years[c_bad_vals[half_bad:]] = -2.5

    raw_df = pd.DataFrame({
        "job_id": job_ids,
        "job_title": job_titles,
        "role_family": role_names,
        "industry": industries,
        "region": regions,
        "city": cities,
        "work_arrangement": work_arrangements,
        "raw_seniority_label": raw_seniority_labels,
        "experience_years": exp_years,
        "raw_posting_date": raw_post_str,
        "raw_closing_date": raw_close_str,
        "raw_salary_min": raw_sal_min_str,
        "raw_salary_max": raw_sal_max_str,
        "views_count": base_views,
        "applications_count": applications,
        "skills_raw": skills_list,
    })

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "uk_job_postings_100k_raw.csv"
    raw_df.to_csv(out_path, index=False)
    print(f"[RAW GENERATOR] Created {len(raw_df):,} unclean UK job postings -> {out_path}")
    return raw_df


if __name__ == "__main__":
    generate_unclean_100k_postings()
