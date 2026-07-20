from __future__ import annotations

from difflib import SequenceMatcher

from models.skill_match_result import SkillMatchResult
from utils.candidate_text_builder import CandidateTextBuilder
from utils.skill_utils import SkillUtils


class SkillMatcher:
    """
    Intelligent ATS-style Skill Matcher.

    Features
    --------
    ✔ Exact matching
    ✔ Synonym matching
    ✔ Partial matching
    ✔ Fuzzy matching
    ✔ Recruiter-style score calibration
    ✔ Preferred skill bonus
    ✔ Rich explainability evidence
    """

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    FUZZY_THRESHOLD = 0.82

    PARTIAL_WEIGHT = 0.60

    PREFERRED_SKILL_WEIGHT = 1.50

    MAX_PREFERRED_BONUS = 10.0

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    @staticmethod
    def score(candidate, job) -> SkillMatchResult:
        """
        Compute overall skill score.

        Parameters
        ----------
        candidate
            Candidate domain object.

        job
            Parsed Job Description.

        Returns
        -------
        SkillMatchResult
        """

        candidate_text = CandidateTextBuilder.build(candidate).lower()

        matched = []

        partial = []

        fuzzy = []

        missing = []

        # -----------------------------------------------------
        # Match every required skill
        # -----------------------------------------------------

        for skill in job.required_skills:

            result = SkillMatcher._match_skill(
                candidate_text,
                skill
            )

            if result == "exact":

                matched.append(skill)

            elif result == "partial":

                partial.append(skill)

            elif result == "fuzzy":

                fuzzy.append(skill)

            else:

                missing.append(skill)

        # -----------------------------------------------------
        # Calculate weighted match ratio
        # -----------------------------------------------------

        total_required = len(job.required_skills)

        if total_required == 0:

            skill_score = 100.0

        else:

            weighted_matches = (
                len(matched)
                + (len(partial) * SkillMatcher.PARTIAL_WEIGHT)
                + (len(fuzzy) * 0.80)
            )

            ratio = weighted_matches / total_required

            skill_score = SkillMatcher._calibrate_score(
                ratio
            )

        # -----------------------------------------------------
        # Preferred Skills
        # -----------------------------------------------------

        preferred_matched = []

        if job.preferred_skills:

            for skill in job.preferred_skills:

                result = SkillMatcher._match_skill(
                    candidate_text,
                    skill
                )

                if result != "none":

                    preferred_matched.append(skill)

            bonus = min(

                SkillMatcher.MAX_PREFERRED_BONUS,

                len(preferred_matched)
                * SkillMatcher.PREFERRED_SKILL_WEIGHT

            )

            skill_score = min(
                100.0,
                skill_score + bonus
            )

        else:

            bonus = 0.0

        skill_score = round(
            skill_score,
            2
        )

        # -----------------------------------------------------
        # Human-readable explanation
        # -----------------------------------------------------

        reason = SkillMatcher._build_reason(

            matched=matched,

            partial=partial,

            fuzzy=fuzzy,

            missing=missing,

            preferred=preferred_matched,

            total=total_required

        )

        # -----------------------------------------------------
        # Structured evidence
        # -----------------------------------------------------

        evidence = {

            "required_total": total_required,

            "required_exact": len(matched),

            "required_partial": len(partial),

            "required_fuzzy": len(fuzzy),

            "required_missing": len(missing),

            "matched_skills": sorted(matched),

            "partial_skills": sorted(partial),

            "fuzzy_skills": sorted(fuzzy),

            "missing_skills": sorted(missing),

            "preferred_total": len(job.preferred_skills),

            "preferred_matched": sorted(preferred_matched),

            "preferred_bonus_applied": round(
                bonus,
                2
            ),

            "weighted_ratio": round(
                (
                    (
                        len(matched)
                        + len(partial) * SkillMatcher.PARTIAL_WEIGHT
                        + len(fuzzy) * 0.80
                    )
                    / total_required
                ) if total_required else 1.0,
                3
            ),

        }

        return SkillMatchResult(

            score=skill_score,

            reason=reason,

            evidence=evidence,

            matched_skills=sorted(matched),

            missing_skills=sorted(missing),

        )

    # ---------------------------------------------------------
    # Skill Matching Engine
    # ---------------------------------------------------------

    @staticmethod
    def _match_skill(
        candidate_text: str,
        skill: str,
    ) -> str:
        """
        Returns one of

        exact
        partial
        fuzzy
        none
        """

        skill = skill.lower().strip()

        # -----------------------------------------
        # Exact Match
        # -----------------------------------------

        if SkillUtils.contains(
            candidate_text,
            skill,
        ):
            return "exact"

        # -----------------------------------------
        # Partial Match
        # -----------------------------------------

        if SkillUtils.partial_contains(
            candidate_text,
            skill,
        ):
            return "partial"

        # -----------------------------------------
        # Fuzzy Match
        # -----------------------------------------

        if SkillMatcher._fuzzy_contains(
            candidate_text,
            skill,
        ):
            return "fuzzy"

        return "none"

    # ---------------------------------------------------------
    # Recruiter Style Calibration
    # ---------------------------------------------------------

    @staticmethod
    def _calibrate_score(
        ratio: float,
    ) -> float:

        if ratio >= 0.95:
            return 100

        elif ratio >= 0.90:
            return 98

        elif ratio >= 0.85:
            return 95

        elif ratio >= 0.80:
            return 92

        elif ratio >= 0.75:
            return 89

        elif ratio >= 0.70:
            return 86

        elif ratio >= 0.65:
            return 83

        elif ratio >= 0.60:
            return 80

        elif ratio >= 0.55:
            return 76

        elif ratio >= 0.50:
            return 72

        elif ratio >= 0.45:
            return 68

        elif ratio >= 0.40:
            return 64

        elif ratio >= 0.35:
            return 60

        elif ratio >= 0.30:
            return 55

        elif ratio >= 0.25:
            return 50

        elif ratio >= 0.20:
            return 45

        elif ratio >= 0.15:
            return 40

        elif ratio >= 0.10:
            return 35

        return 25

    # ---------------------------------------------------------
    # Fuzzy Matching
    # ---------------------------------------------------------

    @staticmethod
    def _fuzzy_contains(
        text: str,
        skill: str,
    ) -> bool:

        words = text.split()

        skill_words = skill.split()

        n = len(skill_words)

        if n == 0:
            return False

        # Sliding window over candidate text

        for i in range(len(words) - n + 1):

            phrase = " ".join(
                words[i:i+n]
            )

            similarity = SequenceMatcher(
                None,
                phrase,
                skill,
            ).ratio()

            if similarity >= SkillMatcher.FUZZY_THRESHOLD:
                return True

        return False

    # ---------------------------------------------------------
    # Human Readable Explanation
    # ---------------------------------------------------------

    @staticmethod
    def _build_reason(
        matched: list[str],
        partial: list[str],
        fuzzy: list[str],
        missing: list[str],
        preferred: list[str],
        total: int,
    ) -> str:
        """
        Generate a recruiter-friendly explanation describing why
        the candidate received this skill score.
        """

        if total == 0:
            return (
                "No required skills were specified in the Job "
                "Description. Candidate receives full skill score."
            )

        pieces = []

        # -----------------------------------------------------
        # Exact Matches
        # -----------------------------------------------------

        if matched:

            preview = ", ".join(matched[:3])

            if len(matched) > 3:
                preview += "..."

            pieces.append(
                f"Matched {len(matched)}/{total} required skills ({preview})"
            )

        # -----------------------------------------------------
        # Partial Matches
        # -----------------------------------------------------

        if partial:

            preview = ", ".join(partial[:3])

            if len(partial) > 3:
                preview += "..."

            pieces.append(
                f"{len(partial)} partially matched ({preview})"
            )

        # -----------------------------------------------------
        # Fuzzy Matches
        # -----------------------------------------------------

        if fuzzy:

            preview = ", ".join(fuzzy[:3])

            if len(fuzzy) > 3:
                preview += "..."

            pieces.append(
                f"{len(fuzzy)} closely related skill(s) detected ({preview})"
            )

        # -----------------------------------------------------
        # Missing Skills
        # -----------------------------------------------------

        if missing:

            preview = ", ".join(missing[:3])

            if len(missing) > 3:
                preview += "..."

            pieces.append(
                f"Missing {len(missing)} required skill(s) ({preview})"
            )

        # -----------------------------------------------------
        # Preferred Skills
        # -----------------------------------------------------

        if preferred:

            preview = ", ".join(preferred[:3])

            if len(preferred) > 3:
                preview += "..."

            pieces.append(
                f"Matched {len(preferred)} preferred skill(s) ({preview})"
            )

        if not pieces:
            return "No significant skill evidence found."

        return ". ".join(pieces) + "."

    # ---------------------------------------------------------
    # Utility Functions
    # ---------------------------------------------------------

    @staticmethod
    def _normalize(skill: str) -> str:
        """
        Normalize skill names before comparison.
        """

        return (
            skill.lower()
            .replace("-", " ")
            .replace("_", " ")
            .strip()
        )
