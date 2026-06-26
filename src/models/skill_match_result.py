from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.match_score import MatchScore


@dataclass
class SkillMatchResult(MatchScore):
    """
    Extends MatchScore with skill-specific evidence fields.

    Inherits from MatchScore so the HybridMatcher can consume every
    matcher result through a uniform interface while preserving the
    domain-specific fields (matched_skills, missing_skills) for the
    Explainability Engine.

    Parameters (in addition to MatchScore fields)
    -----------------------------------------------
    matched_skills : list[str]
        Skills from the JD that were found in the candidate profile.
    missing_skills : list[str]
        Required skills from the JD that were not found.
    """

    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"SkillMatchResult("
            f"score={self.score:.2f}, "
            f"matched={len(self.matched_skills)}, "
            f"missing={len(self.missing_skills)})"
        )