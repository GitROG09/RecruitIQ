from models.candidate import Candidate
from models.profile import Profile
from models.career import Career
from models.skill import Skill
from models.signals import RedrobSignals


class CandidateFactory:
    """
    Converts raw JSON into Candidate domain objects.
    """

    @staticmethod
    def create(raw_candidate: dict) -> Candidate:

        profile = Profile(
            anonymized_name=raw_candidate["profile"]["anonymized_name"],
            headline=raw_candidate["profile"]["headline"],
            summary=raw_candidate["profile"]["summary"],
            location=raw_candidate["profile"]["location"],
            country=raw_candidate["profile"]["country"],
            years_of_experience=raw_candidate["profile"]["years_of_experience"],
            current_title=raw_candidate["profile"]["current_title"],
            current_company=raw_candidate["profile"]["current_company"],
            current_company_size=raw_candidate["profile"]["current_company_size"],
            current_industry=raw_candidate["profile"]["current_industry"],
        )

        careers = []

        for item in raw_candidate["career_history"]:

            careers.append(
                Career(
                    company=item["company"],
                    title=item["title"],
                    start_date=item["start_date"],
                    end_date=item["end_date"],
                    duration_months=item["duration_months"],
                    is_current=item["is_current"],
                    industry=item["industry"],
                    company_size=item["company_size"],
                    description=item["description"],
                )
            )

        skills = []

        for skill in raw_candidate["skills"]:

            skills.append(
                Skill(
                    name=skill["name"],
                    proficiency=skill["proficiency"],
                    endorsements=skill["endorsements"],
                    duration_months=skill["duration_months"],
                )
            )

        signals = RedrobSignals(**raw_candidate["redrob_signals"])

        return Candidate(
            candidate_id=raw_candidate["candidate_id"],
            profile=profile,
            career_history=careers,
            education=raw_candidate["education"],
            skills=skills,
            certifications=raw_candidate["certifications"],
            languages=raw_candidate["languages"],
            redrob_signals=signals,
        )