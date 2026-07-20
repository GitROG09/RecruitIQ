import re

from knowledge.skills import SKILL_ALIASES
from knowledge.roles import ROLE_ALIASES


class JDNormalizer:
    """
    Normalizes raw Job Description text while preserving
    important information like experience ranges.
    """

    @staticmethod
    def normalize(text: str) -> str:

        # Lowercase
        text = text.lower()

        # Normalize whitespace only
        text = re.sub(r"\s+", " ", text)

        # Replace skill aliases using whole-word matching
        for alias, canonical in SKILL_ALIASES.items():

            pattern = r"\b" + re.escape(alias) + r"\b"

            text = re.sub(pattern, canonical, text)

        # Replace role aliases using whole-word matching
        for alias, canonical in ROLE_ALIASES.items():

            pattern = r"\b" + re.escape(alias) + r"\b"

            text = re.sub(pattern, canonical, text)

        return text.strip()