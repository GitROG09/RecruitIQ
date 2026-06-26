import re


class SkillUtils:

    @staticmethod
    def contains(text: str, skill: str) -> bool:

        pattern = r"\b" + re.escape(skill.lower()) + r"\b"

        return re.search(pattern, text) is not None