from __future__ import annotations

from models.match_score import MatchScore
from config.scoring import EXPERIENCE_SCORING


class ExperienceMatcher:
    """
    Computes how well a candidate's total years of experience
    matches the required JD range.

    Scoring formula (unchanged from original):
    - Exact fit (within range)  → 100
    - Under-experienced         → 100 − (gap × penalty_per_year), floor 0
    - Over-qualified            → 100 − (gap × penalty_per_year), floor 60

    All penalty values are read from ``config.scoring.EXPERIENCE_SCORING``
    so they can be tuned without touching this file.
    """

    @staticmethod
    def score(
        candidate_years: float,
        min_exp: float,
        max_exp: float,
    ) -> MatchScore:
        """
        Evaluate experience fit and return a structured MatchScore.

        Parameters
        ----------
        candidate_years : float
            Total years of professional experience.
        min_exp : float
            Minimum years required by the JD.
        max_exp : float
            Maximum years preferred by the JD.

        Returns
        -------
        MatchScore
            score   – [0, 100] fit score
            reason  – one-line human-readable explanation
            evidence – structured signals for the Explainability Engine
        """

        under_penalty = EXPERIENCE_SCORING["under_experience_penalty_per_year"]
        over_penalty  = EXPERIENCE_SCORING["over_experience_penalty_per_year"]
        over_floor    = EXPERIENCE_SCORING["over_experience_floor"]

        # ------------------------------------------------------------------
        # Case 1 — Exact fit
        # ------------------------------------------------------------------
        if min_exp <= candidate_years <= max_exp:
            return MatchScore(
                score=100.0,
                reason=(
                    f"Candidate has {candidate_years}y experience — "
                    f"within the required {min_exp}–{max_exp}y range."
                ),
                evidence={
                    "candidate_years": candidate_years,
                    "required_min": min_exp,
                    "required_max": max_exp,
                    "fit_type": "exact",
                    "gap_years": 0.0,
                },
            )

        # ------------------------------------------------------------------
        # Case 2 — Under-experienced
        # ------------------------------------------------------------------
        if candidate_years < min_exp:
            gap = round(min_exp - candidate_years, 2)
            raw_score = 100.0 - gap * under_penalty
            final_score = max(0.0, raw_score)

            return MatchScore(
                score=final_score,
                reason=(
                    f"Candidate has {candidate_years}y experience — "
                    f"{gap}y below the minimum {min_exp}y required."
                ),
                evidence={
                    "candidate_years": candidate_years,
                    "required_min": min_exp,
                    "required_max": max_exp,
                    "fit_type": "under",
                    "gap_years": gap,
                    "penalty_applied": round(gap * under_penalty, 2),
                },
            )

        # ------------------------------------------------------------------
        # Case 3 — Over-qualified
        # ------------------------------------------------------------------
        gap = round(candidate_years - max_exp, 2)
        raw_score = 100.0 - gap * over_penalty
        final_score = max(over_floor, raw_score)

        return MatchScore(
            score=final_score,
            reason=(
                f"Candidate has {candidate_years}y experience — "
                f"{gap}y above the maximum {max_exp}y preferred. "
                f"Likely over-qualified but still considered."
            ),
            evidence={
                "candidate_years": candidate_years,
                "required_min": min_exp,
                "required_max": max_exp,
                "fit_type": "over",
                "gap_years": gap,
                "penalty_applied": round(gap * over_penalty, 2),
                "score_floored_at": over_floor,
            },
        )