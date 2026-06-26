# =============================================================================
# RecruitIQ — Scoring Configuration
# =============================================================================
# All weights are used as multipliers against a [0–100] dimension score.
# Top-level weights must sum to 1.0.
# Sub-weights within each matcher must sum to 1.0.
# =============================================================================

# -----------------------------------------------------------------------------
# Top-level matcher weights
# -----------------------------------------------------------------------------

MATCH_WEIGHTS: dict[str, float] = {

    "experience": 0.20,

    "skills": 0.25,

    "career": 0.20,

    "behaviour": 0.15,

    "recruiter": 0.10,

    "semantic": 0.10,
}

# -----------------------------------------------------------------------------
# ExperienceMatcher sub-weights
# Signals: exact fit inside the range vs. gap penalty
# (formula-driven — no sub-weights needed; kept here for documentation)
# -----------------------------------------------------------------------------

EXPERIENCE_SCORING: dict[str, float] = {
    "under_experience_penalty_per_year": 20.0,  # points lost per year below min
    "over_experience_penalty_per_year": 5.0,    # points lost per year above max
    "over_experience_floor": 60.0,              # minimum score when over-qualified
}

# -----------------------------------------------------------------------------
# CareerMatcher sub-weights
# Signals: title relevance, industry alignment, tenure stability,
#          seniority progression, company-size breadth
# -----------------------------------------------------------------------------

CAREER_WEIGHTS: dict[str, float] = {
    "title_relevance": 0.35,
    "industry_alignment": 0.25,
    "tenure_stability": 0.20,
    "seniority_progression": 0.15,
    "company_size_breadth": 0.05,
}

# Tenure thresholds (months)
CAREER_TENURE: dict[str, float] = {
    "ideal_min_months": 12,    # below this is considered short-tenure
    "ideal_max_months": 48,    # above this earns full tenure score
    "job_hop_threshold": 6,    # roles shorter than this are flagged
}

# -----------------------------------------------------------------------------
# BehaviourMatcher sub-weights
# Signals: profile completeness, activity recency, open-to-work,
#          assessment scores, interview/offer completion, github activity
# -----------------------------------------------------------------------------

BEHAVIOUR_WEIGHTS: dict[str, float] = {
    "profile_completeness": 0.20,
    "activity_recency": 0.20,
    "open_to_work": 0.10,
    "assessment_scores": 0.20,
    "interview_offer_rates": 0.15,
    "github_activity": 0.15,
}

# How many days of inactivity before recency score starts decaying
BEHAVIOUR_RECENCY: dict[str, int] = {
    "fresh_days": 7,       # full score
    "stale_days": 90,      # score halved
    "inactive_days": 180,  # minimum score
}

# -----------------------------------------------------------------------------
# RecruiterMatcher sub-weights
# Signals: salary fit, notice period fit, work-mode alignment,
#          relocation willingness, verification status
# -----------------------------------------------------------------------------

RECRUITER_WEIGHTS: dict[str, float] = {
    "salary_fit": 0.30,
    "notice_period_fit": 0.25,
    "work_mode_alignment": 0.20,
    "relocation_willingness": 0.15,
    "verification_status": 0.10,
}

# Notice period scoring thresholds (days)
RECRUITER_NOTICE: dict[str, int] = {
    "ideal_max_days": 30,    # full score
    "acceptable_days": 60,   # partial score
    "maximum_days": 90,      # minimum score; above this penalised heavily
}

# -----------------------------------------------------------------------------
# SemanticMatcher config
# -----------------------------------------------------------------------------

SEMANTIC_CONFIG: dict[str, object] = {
    "model_name": "all-MiniLM-L6-v2",
    "similarity_threshold": 0.0,   # floor — anything below maps to 0 score
    "cache_dir": None,             # None → sentence-transformers default cache
}