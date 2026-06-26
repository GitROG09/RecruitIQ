from __future__ import annotations

from typing import Any

from models.match_result import MatchResult
from models.match_score import MatchScore
from config.scoring import MATCH_WEIGHTS

from matching.experience_matcher import ExperienceMatcher
from matching.skill_matcher import SkillMatcher
from matching.career_matcher import CareerMatcher
from matching.behaviour_matcher import BehaviourMatcher
from matching.recruiter_matcher import RecruiterMatcher
from matching.semantic_matcher import SemanticMatcher


class HybridMatcher:
    """
    Aggregates the six specialist matchers into a single weighted score.

    Each matcher returns a ``MatchScore`` (or subclass) carrying a numeric
    score, a human-readable reason, and a structured evidence dict. The
    HybridMatcher collects these, applies the weights from
    ``config.scoring.MATCH_WEIGHTS``, and produces a ``MatchResult`` whose
    ``reasoning`` list preserves every matcher's output for the
    Explainability Engine — no re-computation required downstream.

    Scoring weights (configurable via config/scoring.py):
    -------------------------------------------------------
    experience : 0.20
    skills     : 0.25
    career     : 0.20
    behaviour  : 0.15
    recruiter  : 0.10
    semantic   : 0.10
    """

    def match(
        self,
        candidate,
        feature_vector,
        job,
    ) -> MatchResult:
        """
        Run all six matchers and return a fully scored ``MatchResult``.

        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.
        feature_vector : CandidateFeatureVector
            Pre-computed feature vector from ``CandidateAnalyzer``.
        job : JobDescription
            The parsed job description.

        Returns
        -------
        MatchResult
            Contains all six dimension scores, the weighted overall score,
            and the full reasoning list for downstream explainability.
        """

        # ----------------------------------------------------------------
        # Run all six matchers
        # ----------------------------------------------------------------

        exp_result      = ExperienceMatcher.score(
            candidate_years=feature_vector.experience,
            min_exp=job.experience_min,
            max_exp=job.experience_max,
        )

        skill_result    = SkillMatcher.score(candidate, job)

        career_result   = CareerMatcher.score(candidate, job)

        behaviour_result = BehaviourMatcher.score(candidate, job)

        recruiter_result = RecruiterMatcher.score(candidate, job)

        semantic_result  = SemanticMatcher.score(candidate, job)

        # ----------------------------------------------------------------
        # Weighted composite score
        # ----------------------------------------------------------------

        w = MATCH_WEIGHTS

        overall_score = (
            exp_result.score       * w["experience"]
            + skill_result.score   * w["skills"]
            + career_result.score  * w["career"]
            + behaviour_result.score * w["behaviour"]
            + recruiter_result.score * w["recruiter"]
            + semantic_result.score  * w["semantic"]
        )

        # ----------------------------------------------------------------
        # Structured reasoning list (one entry per matcher)
        # ----------------------------------------------------------------

        reasoning = self._build_reasoning(
            exp_result,
            skill_result,
            career_result,
            behaviour_result,
            recruiter_result,
            semantic_result,
            w,
        )

        # ----------------------------------------------------------------
        # Assemble MatchResult
        # ----------------------------------------------------------------

        return MatchResult(
            candidate_id=candidate.candidate_id,
            experience_score=round(exp_result.score, 2),
            skill_score=round(skill_result.score, 2),
            career_score=round(career_result.score, 2),
            behaviour_score=round(behaviour_result.score, 2),
            recruiter_score=round(recruiter_result.score, 2),
            semantic_score=round(semantic_result.score, 2),
            overall_score=round(overall_score, 2),
            reasoning=reasoning,
        )

    # ====================================================================
    # Private helpers
    # ====================================================================

    @staticmethod
    def _build_reasoning(
        exp: MatchScore,
        skill: MatchScore,
        career: MatchScore,
        behaviour: MatchScore,
        recruiter: MatchScore,
        semantic: MatchScore,
        weights: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Construct the structured reasoning list.

        Each entry is a self-contained dict that includes the matcher name,
        its raw score, its configured weight, the weighted contribution,
        the human-readable reason, and the full evidence payload.
        The Explainability Engine can use any subset of these fields
        without re-running any matcher.
        """

        matchers = [
            ("experience", exp,       weights["experience"]),
            ("skills",     skill,     weights["skills"]),
            ("career",     career,    weights["career"]),
            ("behaviour",  behaviour, weights["behaviour"]),
            ("recruiter",  recruiter, weights["recruiter"]),
            ("semantic",   semantic,  weights["semantic"]),
        ]

        reasoning = []

        for name, result, weight in matchers:
            reasoning.append({
                "matcher":              name,
                "score":                round(result.score, 2),
                "weight":               weight,
                "weighted_contribution": round(result.score * weight, 2),
                "reason":               result.reason,
                "evidence":             result.evidence,
            })

        return reasoning