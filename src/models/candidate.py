from models.profile import Profile
from models.career import Career
from models.skill import Skill
from models.signals import RedrobSignals


class Candidate:
    """
    Main Candidate domain object.
    """

    def __init__(
        self,
        candidate_id: str,
        profile: Profile,
        career_history: list[Career],
        education: list,
        skills: list[Skill],
        certifications: list,
        languages: list,
        redrob_signals: RedrobSignals,
    ):

        self.candidate_id = candidate_id

        self.profile = profile

        self.career_history = career_history

        self.education = education

        self.skills = skills

        self.certifications = certifications

        self.languages = languages

        self.redrob_signals = redrob_signals