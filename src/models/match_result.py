from __future__ import annotations

from typing import Any


class MatchResult:
    """
    Represents the final matching result between a candidate and a job.

    Holds every dimension score, the weighted overall score, the
    candidate_id for traceability, and the structured reasoning list
    consumed by the Explainability Engine.

    Parameters
    ----------
    candidate_id : str
        Identifier of the candidate this result belongs to.
    experience_score : float
        Raw score [0–100] from ExperienceMatcher.
    skill_score : float
        Raw score [0–100] from SkillMatcher.
    career_score : float
        Raw score [0–100] from CareerMatcher.
    behaviour_score : float
        Raw score [0–100] from BehaviourMatcher.
    recruiter_score : float
        Raw score [0–100] from RecruiterMatcher.
    semantic_score : float
        Raw score [0–100] from SemanticMatcher.
    overall_score : float
        Weighted aggregate score [0–100].
    reasoning : list[dict[str, Any]]
        List of structured evidence dicts, one per matcher.
        Each dict has at minimum: ``{"matcher": str, "score": float,
        "reason": str, "evidence": dict}``.
    """

    def __init__(
        self,
        candidate_id: str,
        experience_score: float,
        skill_score: float,
        career_score: float,
        behaviour_score: float,
        recruiter_score: float,
        semantic_score: float,
        overall_score: float,
        reasoning: list[dict[str, Any]] | None = None,
    ):
        self.candidate_id = candidate_id

        self.experience_score = experience_score
        self.skill_score = skill_score
        self.career_score = career_score
        self.behaviour_score = behaviour_score
        self.recruiter_score = recruiter_score
        self.semantic_score = semantic_score

        self.overall_score = round(float(overall_score), 2)

        self.reasoning: list[dict[str, Any]] = reasoning or []

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise to a flat dict for CSV output and logging.

        The ``reasoning`` field is collapsed into a single
        human-readable ``explanation`` string for the CSV.
        """
        explanation = " | ".join(
            r.get("reason", "") for r in self.reasoning
        )

        return {
            "candidate_id": self.candidate_id,
            "overall_score": self.overall_score,
            "experience_score": self.experience_score,
            "skill_score": self.skill_score,
            "career_score": self.career_score,
            "behaviour_score": self.behaviour_score,
            "recruiter_score": self.recruiter_score,
            "semantic_score": self.semantic_score,
            "explanation": explanation,
        }

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"MatchResult("
            f"candidate_id={self.candidate_id!r}, "
            f"overall={self.overall_score:.2f})"
        )