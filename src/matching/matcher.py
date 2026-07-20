from __future__ import annotations

from statistics import mean
from typing import Any

import config.scoring as scoring_config
from matching.behaviour_matcher import BehaviourMatcher
from matching.career_matcher import CareerMatcher
from matching.experience_matcher import ExperienceMatcher
from matching.recruiter_matcher import RecruiterMatcher
from matching.semantic_matcher import SemanticMatcher
from matching.skill_matcher import SkillMatcher
from models.match_result import MatchResult
from models.match_score import MatchScore


class HybridMatcher:
    """
    Intelligent Hybrid Matcher

    Instead of simply averaging matcher scores,
    this matcher rewards consistent candidates while
    penalizing critical weaknesses.
    """

    def match(
        self,
        candidate,
        feature_vector,
        job,
        weights: dict[str, float] | None = None,
    ) -> MatchResult:
        """
        Parameters
        ----------
        weights : dict[str, float] | None
            Per-call weight overrides (e.g. from the Streamlit sidebar
            sliders). If omitted, falls back to the module-level
            ``config.scoring.MATCH_WEIGHTS`` default.

            IMPORTANT: this is passed explicitly rather than mutating
            ``config.scoring.MATCH_WEIGHTS`` in place. Streamlit apps run
            as a single shared process across all users' sessions —
            mutating a module-level global here would let one user's
            slider values leak into another user's concurrent ranking
            run. Always pass weights through the call chain instead of
            patching global config at runtime.
        """

        # -------------------------------------------------------
        # Individual Matchers
        # -------------------------------------------------------

        exp_result = ExperienceMatcher.score(
            candidate_years=feature_vector.experience,
            min_exp=job.experience_min,
            max_exp=job.experience_max,
        )

        skill_result = SkillMatcher.score(
            candidate,
            job,
        )

        career_result = CareerMatcher.score(
            candidate,
            job,
        )

        behaviour_result = BehaviourMatcher.score(
            candidate,
            job,
        )

        recruiter_result = RecruiterMatcher.score(
            candidate,
            job,
        )

        semantic_result = SemanticMatcher.score(
            candidate,
            job,
        )

        # -------------------------------------------------------
        # Weighted Base Score
        # -------------------------------------------------------

        w = weights if weights is not None else scoring_config.MATCH_WEIGHTS

        base_score = (

            exp_result.score * w["experience"]

            + skill_result.score * w["skills"]

            + career_result.score * w["career"]

            + behaviour_result.score * w["behaviour"]

            + recruiter_result.score * w["recruiter"]

            + semantic_result.score * w["semantic"]

        )

        # -------------------------------------------------------
        # Consistency Bonus
        # -------------------------------------------------------

        scores = [

            exp_result.score,

            skill_result.score,

            career_result.score,

            behaviour_result.score,

            recruiter_result.score,

            semantic_result.score,

        ]

        consistency_bonus = sum(

            score >= 80

            for score in scores

        ) * 0.75

        # -------------------------------------------------------
        # Critical Skill Penalty
        # -------------------------------------------------------

        penalty = 0.0

        if skill_result.score < 45:
            penalty += 5

        if semantic_result.score < 45:
            penalty += 5

        if career_result.score < 40:
            penalty += 2

        # -------------------------------------------------------
        # Experience Boost
        # -------------------------------------------------------

        experience_bonus = 0

        if (

            exp_result.score >= 90

            and semantic_result.score >= 85

        ):

            experience_bonus = 2

        # -------------------------------------------------------
        # Balanced Candidate Bonus
        # -------------------------------------------------------

        score_variance = max(scores) - min(scores)

        balanced_bonus = 0

        if score_variance <= 15:

            balanced_bonus = 2

        elif score_variance <= 25:

            balanced_bonus = 1

        # -------------------------------------------------------
        # Final Score
        # -------------------------------------------------------

        overall_score = (

            base_score

            + consistency_bonus

            + experience_bonus

            + balanced_bonus

            - penalty

        )

        overall_score = max(

            0,

            min(

                100,

                round(overall_score, 2)

            )

        )

        reasoning = self._build_reasoning(

            exp_result,

            skill_result,

            career_result,

            behaviour_result,

            recruiter_result,

            semantic_result,

            w,

            base_score,

            consistency_bonus,

            experience_bonus,

            balanced_bonus,

            penalty,

            overall_score,

        )

        return MatchResult(

            candidate_id=candidate.candidate_id,

            experience_score=round(exp_result.score, 2),

            skill_score=round(skill_result.score, 2),

            career_score=round(career_result.score, 2),

            behaviour_score=round(behaviour_result.score, 2),

            recruiter_score=round(recruiter_result.score, 2),

            semantic_score=round(semantic_result.score, 2),

            overall_score=overall_score,

            reasoning=reasoning,

        )
    # ===============================================================
    # Explainability Engine
    # ===============================================================

    @staticmethod
    def _build_reasoning(
        exp: MatchScore,
        skill: MatchScore,
        career: MatchScore,
        behaviour: MatchScore,
        recruiter: MatchScore,
        semantic: MatchScore,
        weights: dict[str, float],
        base_score: float,
        consistency_bonus: float,
        experience_bonus: float,
        balanced_bonus: float,
        penalty: float,
        overall_score: float,
    ) -> list[dict[str, Any]]:

        reasoning = []

        matchers = [

            ("Experience", exp, weights["experience"]),

            ("Skills", skill, weights["skills"]),

            ("Career", career, weights["career"]),

            ("Behaviour", behaviour, weights["behaviour"]),

            ("Recruiter", recruiter, weights["recruiter"]),

            ("Semantic", semantic, weights["semantic"]),

        ]

        for name, result, weight in matchers:

            reasoning.append({

                "matcher": name,

                "score": round(result.score, 2),

                "weight": weight,

                "weighted_contribution": round(

                    result.score * weight,

                    2,

                ),

                "reason": result.reason,

                "evidence": result.evidence,

            })

        # ---------------------------------------------------------
        # Overall Summary
        # ---------------------------------------------------------

        if overall_score >= 90:

            overall_rating = "Excellent"

        elif overall_score >= 80:

            overall_rating = "Strong"

        elif overall_score >= 70:

            overall_rating = "Good"

        elif overall_score >= 60:

            overall_rating = "Average"

        else:

            overall_rating = "Weak"

        reasoning.append({

            "matcher": "Overall Assessment",

            "score": round(overall_score, 2),

            "weight": 1.0,

            "weighted_contribution": round(overall_score, 2),

            "reason": (

                f"Overall candidate rating: {overall_rating}"

            ),

            "evidence": {

                "base_score": round(base_score, 2),

                "consistency_bonus": consistency_bonus,

                "experience_bonus": experience_bonus,

                "balanced_bonus": balanced_bonus,

                "penalty": penalty,

                "overall_rating": overall_rating,

                "overall_score": round(overall_score, 2),

            },

        })

        return reasoning
