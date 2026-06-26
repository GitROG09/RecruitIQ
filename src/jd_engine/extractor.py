import re

from knowledge.canonical_skills import CANONICAL_SKILLS
from knowledge.behaviour import BEHAVIOUR_KEYWORDS


class JDExtractor:
    """
    Extracts structured information from a normalized
    Job Description.
    """

    ROLES = [
        "machine learning engineer",
        "artificial intelligence engineer",
        "data scientist",
        "backend engineer",
        "software engineer",
        "search engineer",
    ]

    @staticmethod
    def extract_role(text: str) -> str:
        """
        Extract the job role.
        """

        for role in JDExtractor.ROLES:
            pattern = r"\b" + re.escape(role) + r"\b"

            if re.search(pattern, text):
                return role

        return "unknown"

    @staticmethod
    def extract_experience(text: str):
        """
        Extract experience requirements from the JD.

        Supported formats:
            5-9 years
            5 – 9 years
            5+ years
            minimum 5 years
            at least 5 years
        """

        text = text.lower()

        # 5-9 years
        match = re.search(
            r"(\d+)\s*(?:-|–)\s*(\d+)\s*years?",
            text,
            re.IGNORECASE
        )

        if match:
            return float(match.group(1)), float(match.group(2))

        # 5+ years
        match = re.search(r"(\d+)\s*\+\s*years?", text)

        if match:
            return float(match.group(1)), 100.0

        # minimum 5 years
        match = re.search(r"minimum\s+(\d+)\s*years?", text)

        if match:
            return float(match.group(1)), 100.0

        # at least 5 years
        match = re.search(r"at\s+least\s+(\d+)\s*years?", text)

        if match:
            return float(match.group(1)), 100.0

        return 0.0, 100.0

    @staticmethod
    def extract_skills(text: str):
        """
        Extract canonical skills from the JD.
        """

        found_skills = []

        for skill in CANONICAL_SKILLS:

            pattern = r"\b" + re.escape(skill) + r"\b"

            if re.search(pattern, text):
                found_skills.append(skill)

        return sorted(found_skills)

    @staticmethod
    def extract_behaviour(text: str):
        """
        Extract behavioural traits.
        """

        found_traits = []

        for trait in BEHAVIOUR_KEYWORDS:

            pattern = r"\b" + re.escape(trait) + r"\b"

            if re.search(pattern, text):
                found_traits.append(trait)

        return sorted(found_traits)