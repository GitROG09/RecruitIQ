from __future__ import annotations

from models.skill_match_result import SkillMatchResult
from utils.candidate_text_builder import CandidateTextBuilder
from utils.skill_utils import SkillUtils


class SkillMatcher:
    """
    Hybrid skill matcher that checks the complete candidate profile
    (headline, summary, job titles, descriptions) rather than only the
    structured skills list, so partial or implicit skill mentions are
    captured.

    Returns a ``SkillMatchResult`` (subclass of ``MatchScore``) carrying
    matched/missing skill lists, a human-readable reason, and a structured
    evidence dict for the Explainability Engine.
    """

    @staticmethod
    def score(candidate, job) -> SkillMatchResult:
        """
        Match required skills from the JD against the full candidate text.

        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.
        job : JobDescription
            The parsed job description.

        Returns
        -------
        SkillMatchResult
            score          – [0, 100] percentage of required skills matched
            reason         – one-line human-readable explanation
            evidence       – structured match details
            matched_skills – skills that were found
            missing_skills – skills that were not found
        """
        candidate_text = CandidateTextBuilder.build(candidate)

        matched: list[str] = []
        missing: list[str] = []

        for skill in job.required_skills:
            if SkillUtils.contains(candidate_text, skill):
                matched.append(skill)
            else:
                missing.append(skill)

        total = len(job.required_skills)

        if total == 0:
            skill_score = 100.0
        else:
            skill_score = (len(matched) / total) * 100.0

        # ------------------------------------------------------------------
        # Preferred-skills bonus — up to +5 points (soft boost, capped at 100)
        # ------------------------------------------------------------------
        preferred_matched: list[str] = []
        if job.preferred_skills:
            preferred_matched = [
                s for s in job.preferred_skills
                if SkillUtils.contains(candidate_text, s)
            ]
            bonus = (len(preferred_matched) / len(job.preferred_skills)) * 5.0
            skill_score = min(100.0, skill_score + bonus)

        skill_score = round(skill_score, 2)

        # ------------------------------------------------------------------
        # Reason
        # ------------------------------------------------------------------
        reason = SkillMatcher._build_reason(
            matched, missing, preferred_matched, total
        )

        # ------------------------------------------------------------------
        # Evidence
        # ------------------------------------------------------------------
        evidence = {
            "required_total": total,
            "required_matched": len(matched),
            "required_missing": len(missing),
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing),
            "preferred_total": len(job.preferred_skills),
            "preferred_matched": sorted(preferred_matched),
            "preferred_bonus_applied": round(
                (len(preferred_matched) / len(job.preferred_skills)) * 5.0, 2
            ) if job.preferred_skills else 0.0,
        }

        return SkillMatchResult(
            score=skill_score,
            reason=reason,
            evidence=evidence,
            matched_skills=sorted(matched),
            missing_skills=sorted(missing),
        )

    # ------------------------------------------------------------------
    # Reason builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reason(
        matched: list,
        missing: list,
        preferred_matched: list,
        total: int,
    ) -> str:
        if total == 0:
            return "No required skills listed in the JD; full score awarded."

        n_matched = len(matched)
        n_missing = len(missing)

        base = (
            f"Matched {n_matched}/{total} required skills"
            f" ({', '.join(matched[:3])}{'...' if n_matched > 3 else ''})"
        )

        if n_missing:
            base += (
                f"; missing: {', '.join(missing[:3])}"
                f"{'...' if n_missing > 3 else ''}"
            )

        if preferred_matched:
            base += (
                f"; also matched {len(preferred_matched)} preferred skill(s)"
                f" ({', '.join(preferred_matched[:2])})"
            )

        return base + "."