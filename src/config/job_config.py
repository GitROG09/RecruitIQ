# =============================================================================
# RecruitIQ — Job Context Defaults
# =============================================================================
# These values are used by RecruiterMatcher when the parsed JobDescription
# does not explicitly specify recruiter-side preferences.
# Override per-job by populating the relevant fields on the JobDescription
# object before passing it to the matcher.
# =============================================================================

JOB_DEFAULTS: dict[str, object] = {

    # Salary range fallback (INR LPA).
    # Set to None to skip salary-fit scoring when unavailable.
    "salary_min_lpa": None,
    "salary_max_lpa": None,

    # Maximum acceptable notice period in days.
    # Candidates within this threshold receive full notice-period score.
    "max_notice_period_days": 60,

    # Preferred work mode: "remote" | "hybrid" | "onsite" | None
    # None means any mode is acceptable (full score for all candidates).
    "preferred_work_mode": None,

    # Whether the job requires willingness to relocate.
    "relocation_required": False,

    # Minimum required profile completeness score (0–100).
    # Used as a soft gate in BehaviourMatcher.
    "min_profile_completeness": 60,
}
