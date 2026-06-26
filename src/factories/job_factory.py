from jd_engine.normalizer import JDNormalizer
from jd_engine.extractor import JDExtractor

from models.job import JobDescription


class JobFactory:

    @staticmethod
    def create(raw_text: str):

        normalized = JDNormalizer.normalize(raw_text)

        role = JDExtractor.extract_role(normalized)

        exp_min, exp_max = JDExtractor.extract_experience(normalized)

        skills = JDExtractor.extract_skills(normalized)

        behaviour = JDExtractor.extract_behaviour(normalized)
        
        return JobDescription(

            role=role,

            experience_min=exp_min,

            experience_max=exp_max,

            required_skills=skills,

            preferred_skills=[],

            responsibilities=[],

            behaviour_traits=behaviour,
        )