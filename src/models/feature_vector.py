class CandidateFeatureVector:
    """
    Stores all engineered features extracted from a candidate.
    """

    def __init__(
        self,
        experience: float,
        companies: int,
        average_tenure: float,
        longest_tenure: int,
        total_skills: int,
        advanced_skills: int,
        average_skill_duration: float,
        total_endorsements: int,
        github_activity_score: float,
    ):

        self.experience = experience

        self.companies = companies

        self.average_tenure = average_tenure

        self.longest_tenure = longest_tenure

        self.total_skills = total_skills

        self.advanced_skills = advanced_skills

        self.average_skill_duration = average_skill_duration

        self.total_endorsements = total_endorsements

        self.github_activity_score = github_activity_score

    def __repr__(self):

        return (
            f"CandidateFeatureVector("
            f"experience={self.experience}, "
            f"skills={self.total_skills})"
        )