from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MatchScore:
    """
    Base result object returned by every matcher in RecruitIQ.

    All specialist matchers subclass this to add domain-specific
    evidence fields while guaranteeing a uniform interface for the
    HybridMatcher and the Explainability Engine.

    Attributes
    ----------
    score : float
        Normalised score in the range [0.0, 100.0].
    reason : str
        One-sentence human-readable summary of the score.
    evidence : dict[str, Any]
        Structured key-value evidence used by the Explainability
        Engine to build rich explanations without re-computation.
        Keys and value types are defined by each subclass.
    """

    score: float
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        """Clamp score to [0.0, 100.0] and validate types."""
        if not isinstance(self.score, (int, float)):
            raise TypeError(
                f"MatchScore.score must be numeric, got {type(self.score)}"
            )
        self.score = round(float(max(0.0, min(100.0, self.score))), 2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise the result to a plain dict for logging and CSV output.
        Subclass fields are included via the overridden version.
        """
        return {
            "score": self.score,
            "reason": self.reason,
            "evidence": self.evidence,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"score={self.score:.2f}, "
            f'reason="{self.reason[:60]}...")'
        )
