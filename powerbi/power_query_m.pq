// =============================================================================
// Intelligent UK Skills Demand Forecasting & Salary Integrity Engine
// Power Query (M) Data Ingestion & Transformation Script
// =============================================================================

let
    // 1. Load Enriched & Validated UK Job Postings Table
    Source = Csv.Document(
        File.Contents("C:\Projects\uk-skills-salary-engine\data\processed\job_postings_clean_sample_10k.csv"),
        [Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    // 2. Enforce Strict Numeric, Currency, and Date Types
    TypedTable = Table.TransformColumnTypes(PromotedHeaders, {
        {"job_id", type text},
        {"job_title", type text},
        {"role_family", type text},
        {"industry", type text},
        {"region", type text},
        {"city", type text},
        {"work_arrangement", type text},
        {"raw_seniority_label", type text},
        {"recalculated_seniority", type text},
        {"is_false_seniority_label", Int64.Type},
        {"experience_years", type number},
        {"posting_date", type date},
        {"closing_date", type date},
        {"listing_duration_days", Int64.Type},
        {"salary_min_gbp", Currency.Type},
        {"salary_max_gbp", Currency.Type},
        {"salary_midpoint_gbp", Currency.Type},
        {"salary_spread_pct", type number},
        {"role_salary_volatility_cv", type number},
        {"posting_attractiveness_score", type number},
        {"views_count", Int64.Type},
        {"applications_count", Int64.Type},
        {"conversion_rate_pct", type number},
        {"skills_count", Int64.Type}
    }),

    // 3. Add Seniority Sort Order for Visual Hierarchy
    AddedSenioritySort = Table.AddColumn(
        TypedTable,
        "SenioritySortOrder",
        each if [recalculated_seniority] = "Junior" then 1
             else if [recalculated_seniority] = "Mid-Level" then 2
             else if [recalculated_seniority] = "Senior" then 3
             else 4,
        Int64.Type
    )
in
    AddedSenioritySort
