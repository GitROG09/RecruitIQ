class RedrobSignals:
    """
    Stores recruiter behaviour and platform signals.
    """

    def __init__(self, **kwargs):

        self.profile_completeness_score = kwargs.get("profile_completeness_score")

        self.signup_date = kwargs.get("signup_date")

        self.last_active_date = kwargs.get("last_active_date")

        self.open_to_work_flag = kwargs.get("open_to_work_flag")

        self.profile_views_received_30d = kwargs.get(
            "profile_views_received_30d"
        )

        self.applications_submitted_30d = kwargs.get(
            "applications_submitted_30d"
        )

        self.recruiter_response_rate = kwargs.get(
            "recruiter_response_rate"
        )

        self.avg_response_time_hours = kwargs.get(
            "avg_response_time_hours"
        )

        self.skill_assessment_scores = kwargs.get(
            "skill_assessment_scores"
        )

        self.connection_count = kwargs.get("connection_count")

        self.endorsements_received = kwargs.get(
            "endorsements_received"
        )

        self.notice_period_days = kwargs.get(
            "notice_period_days"
        )

        self.expected_salary_range_inr_lpa = kwargs.get(
            "expected_salary_range_inr_lpa"
        )

        self.preferred_work_mode = kwargs.get(
            "preferred_work_mode"
        )

        self.willing_to_relocate = kwargs.get(
            "willing_to_relocate"
        )

        self.github_activity_score = kwargs.get(
            "github_activity_score"
        )

        self.search_appearance_30d = kwargs.get(
            "search_appearance_30d"
        )

        self.saved_by_recruiters_30d = kwargs.get(
            "saved_by_recruiters_30d"
        )

        self.interview_completion_rate = kwargs.get(
            "interview_completion_rate"
        )

        self.offer_acceptance_rate = kwargs.get(
            "offer_acceptance_rate"
        )

        self.verified_email = kwargs.get("verified_email")

        self.verified_phone = kwargs.get("verified_phone")

        self.linkedin_connected = kwargs.get(
            "linkedin_connected"
        )