from __future__ import annotations

import re
from typing import Any

from models.match_score import MatchScore
from config.scoring import CAREER_WEIGHTS, CAREER_TENURE
from knowledge.roles import ROLE_ALIASES


# ---------------------------------------------------------------------------
# Seniority ladder — order matters (index = level, higher = more senior)
# ---------------------------------------------------------------------------
_SENIORITY_LADDER: list[list[str]] = [
    ["intern", "trainee", "apprentice"],
    ["junior", "associate", "jr"],
    ["mid", "software engineer", "engineer", "developer", "analyst"],
    ["senior", "sr", "specialist", "ii", "iii"],
    ["lead", "staff", "principal"],
    ["manager", "architect"],
    ["director", "head of"],
    ["vp", "vice president"],
    ["cto", "cpo", "ceo", "chief"],
]


def _seniority_level(title: str) -> int:
    """
    Map a job title to a seniority integer level (0 = intern, 8 = C-suite).
    Returns -1 if the title doesn't match any tier.
    """
    t = title.lower()
    for level, keywords in enumerate(_SENIORITY_LADDER):
        if any(kw in t for kw in keywords):
            return level
    return -1


def _normalise_role(role: str) -> str:
    """Expand known role aliases to their canonical form."""
    key = role.strip().lower()
    return ROLE_ALIASES.get(key, key)


def _title_tokens(title: str) -> set[str]:
    """Return significant word tokens from a job title."""
    stopwords = {
        "and", "of", "the", "at", "in", "for", "a", "an",
        "ii", "iii", "iv", "i",
    }
    tokens = re.findall(r"[a-z]+", title.lower())
    return {t for t in tokens if t not in stopwords and len(t) > 1}


class CareerMatcher:
    """
    Evaluates how well a candidate's career trajectory aligns with the
    target role across five weighted signals:

    1. Title Relevance      (35 %) — past titles vs. JD role
    2. Industry Alignment   (25 %) — past industries vs. JD role keywords
    3. Tenure Stability     (20 %) — penalises job-hopping
    4. Seniority Progression(15 %) — upward trajectory in seniority
    5. Company-Size Breadth ( 5 %) — diversity of company sizes worked at

    All sub-weights are read from ``config.scoring.CAREER_WEIGHTS``.
    """

    @staticmethod
    def score(candidate, job) -> MatchScore:
        """
        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.
        job : JobDescription
            The parsed job description.

        Returns
        -------
        MatchScore
            score    – weighted composite [0, 100]
            reason   – one-line summary for the Explainability Engine
            evidence – per-signal scores and structured details
        """
        careers = candidate.career_history

        if not careers:
            return MatchScore(
                score=0.0,
                reason="No career history available to evaluate.",
                evidence={"careers_count": 0},
            )

        # ----------------------------------------------------------------
        # Signal 1 — Title Relevance
        # ----------------------------------------------------------------
        title_score, title_evidence = CareerMatcher._title_relevance(
            careers, job
        )

        # ----------------------------------------------------------------
        # Signal 2 — Industry Alignment
        # ----------------------------------------------------------------
        industry_score, industry_evidence = CareerMatcher._industry_alignment(
            careers, job
        )

        # ----------------------------------------------------------------
        # Signal 3 — Tenure Stability
        # ----------------------------------------------------------------
        tenure_score, tenure_evidence = CareerMatcher._tenure_stability(
            careers
        )

        # ----------------------------------------------------------------
        # Signal 4 — Seniority Progression
        # ----------------------------------------------------------------
        seniority_score, seniority_evidence = CareerMatcher._seniority_progression(
            careers
        )

        # ----------------------------------------------------------------
        # Signal 5 — Company-Size Breadth
        # ----------------------------------------------------------------
        breadth_score, breadth_evidence = CareerMatcher._company_size_breadth(
            careers
        )

        # ----------------------------------------------------------------
        # Weighted composite
        # ----------------------------------------------------------------
        w = CAREER_WEIGHTS
        composite = (
            title_score    * w["title_relevance"]
            + industry_score * w["industry_alignment"]
            + tenure_score   * w["tenure_stability"]
            + seniority_score * w["seniority_progression"]
            + breadth_score  * w["company_size_breadth"]
        )

        # ----------------------------------------------------------------
        # Build human-readable summary
        # ----------------------------------------------------------------
        reason = CareerMatcher._build_reason(
            title_score, industry_score, tenure_score,
            seniority_score, breadth_score, careers,
        )

        evidence: dict[str, Any] = {
            "careers_count": len(careers),
            "title_relevance": {
                "score": round(title_score, 2),
                "weight": w["title_relevance"],
                **title_evidence,
            },
            "industry_alignment": {
                "score": round(industry_score, 2),
                "weight": w["industry_alignment"],
                **industry_evidence,
            },
            "tenure_stability": {
                "score": round(tenure_score, 2),
                "weight": w["tenure_stability"],
                **tenure_evidence,
            },
            "seniority_progression": {
                "score": round(seniority_score, 2),
                "weight": w["seniority_progression"],
                **seniority_evidence,
            },
            "company_size_breadth": {
                "score": round(breadth_score, 2),
                "weight": w["company_size_breadth"],
                **breadth_evidence,
            },
        }

        return MatchScore(
            score=round(composite, 2),
            reason=reason,
            evidence=evidence,
        )

    # ====================================================================
    # Private signal methods
    # ====================================================================

    @staticmethod
    def _title_relevance(
        careers: list, job
    ) -> tuple[float, dict]:
        """
        Compute overlap between the candidate's past job titles and the
        JD role using token-level Jaccard similarity.

        Best-matching title across all roles is used.
        """
        jd_tokens = _title_tokens(_normalise_role(job.role))

        if not jd_tokens:
            return 50.0, {"note": "JD role was empty; defaulted to 50"}

        best_score = 0.0
        best_title = ""

        for career in careers:
            if not career.title:
                continue

            candidate_tokens = _title_tokens(career.title)
            if not candidate_tokens:
                continue

            intersection = jd_tokens & candidate_tokens
            union = jd_tokens | candidate_tokens
            jaccard = len(intersection) / len(union) if union else 0.0
            sim = jaccard * 100.0

            if sim > best_score:
                best_score = sim
                best_title = career.title

        all_titles = [c.title for c in careers if c.title]

        return best_score, {
            "jd_role": job.role,
            "jd_tokens": sorted(jd_tokens),
            "best_matching_title": best_title,
            "all_titles": all_titles,
        }

    @staticmethod
    def _industry_alignment(
        careers: list, job
    ) -> tuple[float, dict]:
        """
        Check how many of the candidate's past industries contain
        keywords derived from the JD role and responsibilities.
        """
        # Build a keyword set from JD role + responsibilities
        jd_text = (
            job.role.lower()
            + " "
            + " ".join(job.responsibilities).lower()
        )
        jd_words = set(re.findall(r"[a-z]{3,}", jd_text))

        candidate_industries = [
            c.industry.lower()
            for c in careers
            if c.industry
        ]

        if not candidate_industries:
            return 30.0, {"note": "No industry data on candidate careers"}

        # Score = fraction of roles in a relevant industry
        relevant = [
            ind for ind in candidate_industries
            if any(w in ind for w in jd_words)
        ]

        score = (len(relevant) / len(candidate_industries)) * 100.0

        # Partial credit when no direct match — industries listed are real
        if score == 0.0 and candidate_industries:
            score = 25.0

        return score, {
            "candidate_industries": candidate_industries,
            "relevant_industries": relevant,
            "jd_keywords_used": sorted(list(jd_words))[:15],
        }

    @staticmethod
    def _tenure_stability(careers: list) -> tuple[float, dict]:
        """
        Penalise short-tenure roles (job-hopping).

        - Roles ≥ ideal_max_months           → full contribution
        - ideal_min_months ≤ role < ideal_max → partial contribution
        - Roles < job_hop_threshold            → flagged as job-hop
        """
        hop_threshold = CAREER_TENURE["job_hop_threshold"]
        ideal_min     = CAREER_TENURE["ideal_min_months"]
        ideal_max     = CAREER_TENURE["ideal_max_months"]

        if not careers:
            return 0.0, {}

        hop_count   = 0
        role_scores = []

        for career in careers:
            dur = career.duration_months or 0

            if dur >= ideal_max:
                role_scores.append(100.0)
            elif dur >= ideal_min:
                # Linear interpolation between 60 and 100
                frac = (dur - ideal_min) / (ideal_max - ideal_min)
                role_scores.append(60.0 + frac * 40.0)
            elif dur >= hop_threshold:
                role_scores.append(40.0)
            else:
                hop_count += 1
                role_scores.append(0.0)

        avg_score = sum(role_scores) / len(role_scores)

        return avg_score, {
            "total_roles": len(careers),
            "job_hops_flagged": hop_count,
            "hop_threshold_months": hop_threshold,
            "per_role_scores": [round(s, 1) for s in role_scores],
        }

    @staticmethod
    def _seniority_progression(careers: list) -> tuple[float, dict]:
        """
        Detect upward seniority movement across the career timeline.

        Careers are evaluated in chronological order (earliest first).
        A non-decreasing or increasing sequence earns full/partial score.
        """
        # Sort chronologically by start_date (None-safe)
        sorted_careers = sorted(
            careers,
            key=lambda c: (c.start_date or "0000"),
        )

        levels = [
            _seniority_level(c.title or "")
            for c in sorted_careers
            if c.title
        ]

        # Filter out unrecognised titles
        levels = [l for l in levels if l >= 0]

        if len(levels) < 2:
            # Only one measurable role — give benefit of the doubt
            return 60.0, {
                "note": "Insufficient titles for progression analysis",
                "levels_detected": levels,
            }

        increases = sum(
            1 for i in range(1, len(levels)) if levels[i] > levels[i - 1]
        )
        decreases = sum(
            1 for i in range(1, len(levels)) if levels[i] < levels[i - 1]
        )
        transitions = len(levels) - 1

        progression_ratio = increases / transitions if transitions else 0.0
        regression_ratio  = decreases / transitions if transitions else 0.0

        score = max(0.0, (progression_ratio - regression_ratio * 0.5) * 100.0)

        # Ensure at least 50 when final level ≥ starting level
        if levels[-1] >= levels[0]:
            score = max(50.0, score)

        return score, {
            "seniority_levels": levels,
            "increases": increases,
            "decreases": decreases,
            "transitions": transitions,
        }

    @staticmethod
    def _company_size_breadth(careers: list) -> tuple[float, dict]:
        """
        Reward candidates who have experience across diverse company sizes
        (startup + mid-size + enterprise is ideal breadth).
        """
        sizes = {
            c.company_size.lower()
            for c in careers
            if c.company_size
        }

        # Buckets: startup / mid / enterprise
        startup    = any(s in ("startup", "small", "seed", "early-stage") for s in sizes)
        mid        = any(s in ("mid-size", "mid", "medium", "growth") for s in sizes)
        enterprise = any(s in ("enterprise", "large", "corporate", "mnc") for s in sizes)

        bucket_count = sum([startup, mid, enterprise])

        score_map = {0: 30.0, 1: 50.0, 2: 75.0, 3: 100.0}
        score = score_map.get(bucket_count, 30.0)

        return score, {
            "unique_sizes": sorted(sizes),
            "startup_exp": startup,
            "mid_size_exp": mid,
            "enterprise_exp": enterprise,
            "breadth_buckets": bucket_count,
        }

    # ====================================================================
    # Reason builder
    # ====================================================================

    @staticmethod
    def _build_reason(
        title: float,
        industry: float,
        tenure: float,
        seniority: float,
        breadth: float,
        careers: list,
    ) -> str:
        parts = []

        if title >= 70:
            parts.append("strong title alignment")
        elif title >= 40:
            parts.append("partial title alignment")
        else:
            parts.append("low title alignment")

        if industry >= 60:
            parts.append("relevant industry background")
        else:
            parts.append("limited industry overlap")

        if tenure >= 70:
            parts.append("stable tenure")
        else:
            parts.append("some short-tenure roles flagged")

        if seniority >= 60:
            parts.append("positive seniority trajectory")
        else:
            parts.append("non-linear seniority path")

        return (
            f"Career evaluated across {len(careers)} role(s): "
            + ", ".join(parts) + "."
        )
