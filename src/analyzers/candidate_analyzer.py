from models.candidate import Candidate
from models.feature_vector import CandidateFeatureVector
ADVANCED_LEVELS = {"advanced", "expert"}


class CandidateAnalyzer:
    """
    Analyzes a Candidate object and extracts engineered features
    used by the ranking engine.
    """

    def __init__(self, candidate: Candidate):
        self.candidate = candidate

        # Cache frequently used objects
        self.profile = candidate.profile
        self.skills = candidate.skills
        self.careers = candidate.career_history
        self.signals = candidate.redrob_signals

    # ------------------------------------------------------------------
    # Career Features
    # ------------------------------------------------------------------

    def total_experience(self) -> float:
        return self.profile.years_of_experience

    def total_companies(self) -> int:
        return len(self.careers)

    def average_tenure(self) -> float:

        if not self.careers:
            return 0.0

        total = sum(job.duration_months for job in self.careers)

        return round(total / len(self.careers), 2)

    def longest_tenure(self) -> int:

        if not self.careers:
            return 0

        return max(job.duration_months for job in self.careers)

    # ------------------------------------------------------------------
    # Skill Features
    # ------------------------------------------------------------------

    def total_skills(self) -> int:
        return len(self.skills)

    def advanced_skills(self) -> int:

        return sum(
            1
            for skill in self.skills
            if skill.proficiency.lower() in ADVANCED_LEVELS
        )

    def average_skill_duration(self) -> float:

        if not self.skills:
            return 0.0

        total = sum(skill.duration_months for skill in self.skills)

        return round(total / len(self.skills), 2)

    def total_endorsements(self) -> int:

        return sum(skill.endorsements for skill in self.skills)

    # ------------------------------------------------------------------
    # Behaviour Features
    # ------------------------------------------------------------------

    def github_activity_score(self) -> float:
        return self.signals.github_activity_score

    # ------------------------------------------------------------------
    # Feature Vector
    # ------------------------------------------------------------------

    def build_feature_vector(self) -> CandidateFeatureVector:
        """
        Build a structured feature vector.
        """

        return CandidateFeatureVector(

            experience=self.total_experience(),

            companies=self.total_companies(),

            average_tenure=self.average_tenure(),

            longest_tenure=self.longest_tenure(),

            total_skills=self.total_skills(),

            advanced_skills=self.advanced_skills(),

            average_skill_duration=self.average_skill_duration(),

            total_endorsements=self.total_endorsements(),

            github_activity_score=self.github_activity_score(),
        )