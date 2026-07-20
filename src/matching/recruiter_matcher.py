from __future__ import annotations

from typing import Any

from models.match_score import MatchScore
from config.scoring import RECRUITER_WEIGHTS, RECRUITER_NOTICE
from config.job_config import JOB_DEFAULTS


# ---------------------------------------------------------------------------
# Work-mode compatibility matrix
# Rows = candidate preference, Cols = job requirement
# Values = compatibility score [0–100]
# ---------------------------------------------------------------------------
_WORK_MODE_COMPAT: dict[str, dict[str, float]] = {
    "remote":  {"remote": 100.0, "hybrid": 60.0, "onsite": 10.0},
    "hybrid":  {"remote": 70.0,  "hybrid": 100.0, "onsite": 60.0},
    "onsite":  {"remote": 30.0,  "hybrid": 70.0,  "onsite": 100.0},
}


def _normalise_work_mode(value: str | None) -> str | None:
    """Lower-case and strip common synonyms to a canonical mode."""
    if not value:
        return None
    v = str(value).strip().lower()
    if v in ("wfh", "work from home", "fully remote"):
        return "remote"
    if v in ("office", "in-office", "on-site", "in office"):
        return "onsite"
    if v in ("hybrid", "flexible"):
        return "hybrid"
    return v


def _parse_salary_range(value) -> tuple[float, float] | None:
    """
    Extract (min, max) LPA from various input formats:
    - dict  : {"min": 20, "max": 30}
    - list  : [20, 30]
    - float : 25  → treated as both min and max
    - None  : returns None
    """
    if value is None:
        return None
    if isinstance(value, dict):
        lo = value.get("min") or value.get("low") or value.get("minimum")
        hi = value.get("max") or value.get("high") or value.get("maximum")
        if lo is not None and hi is not None:
            return float(lo), float(hi)
        # Single-key dict
        vals = list(value.values())
        if len(vals) == 1:
            v = float(vals[0])
            return v, v
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return float(value[0]), float(value[1])
    try:
        v = float(value)
        return v, v
    except (TypeError, ValueError):
        return None


class RecruiterMatcher:
    """
    Evaluates operational / logistics fit between a candidate and a job
    from the recruiter's perspective.

    Five weighted signals:

    1. Salary Fit           (30 %) — expected salary vs. JD budget range
    2. Notice Period Fit    (25 %) — notice period vs. JD max tolerance
    3. Work-Mode Alignment  (20 %) — preferred work mode vs. JD requirement
    4. Relocation           (15 %) — willingness vs. whether role requires it
    5. Verification Status  (10 %) — email / phone / LinkedIn verified

    All sub-weights are read from ``config.scoring.RECRUITER_WEIGHTS``.
    When the JD does not specify a value, ``config.job_config.JOB_DEFAULTS``
    is used as a fallback.
    """

    @staticmethod
    def score(candidate, job=None) -> MatchScore:
        """
        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.
        job : JobDescription | None
            The parsed job description; None triggers full defaults.

        Returns
        -------
        MatchScore
            score    – weighted composite [0, 100]
            reason   – one-line human-readable summary
            evidence – per-signal scores and structured details
        """
        signals = candidate.redrob_signals

        # ----------------------------------------------------------------
        # Signal 1 — Salary Fit
        # ----------------------------------------------------------------
        salary_score, salary_ev = RecruiterMatcher._salary_fit(signals, job)

        # ----------------------------------------------------------------
        # Signal 2 — Notice Period Fit
        # ----------------------------------------------------------------
        notice_score, notice_ev = RecruiterMatcher._notice_period_fit(
            signals, job
        )

        # ----------------------------------------------------------------
        # Signal 3 — Work-Mode Alignment
        # ----------------------------------------------------------------
        mode_score, mode_ev = RecruiterMatcher._work_mode_alignment(
            signals, job
        )

        # ----------------------------------------------------------------
        # Signal 4 — Relocation Willingness
        # ----------------------------------------------------------------
        reloc_score, reloc_ev = RecruiterMatcher._relocation_fit(signals, job)

        # ----------------------------------------------------------------
        # Signal 5 — Verification Status
        # ----------------------------------------------------------------
        verif_score, verif_ev = RecruiterMatcher._verification_status(signals)

        # ----------------------------------------------------------------
        # Weighted composite
        # ----------------------------------------------------------------
        w = RECRUITER_WEIGHTS
        composite = (
            salary_score * w["salary_fit"]
            + notice_score * w["notice_period_fit"]
            + mode_score   * w["work_mode_alignment"]
            + reloc_score  * w["relocation_willingness"]
            + verif_score  * w["verification_status"]
        )

        reason = RecruiterMatcher._build_reason(
            salary_score, notice_score, mode_score,
            reloc_score, verif_score, signals,
        )

        evidence: dict[str, Any] = {
            "salary_fit": {
                "score": round(salary_score, 2),
                "weight": w["salary_fit"],
                **salary_ev,
            },
            "notice_period_fit": {
                "score": round(notice_score, 2),
                "weight": w["notice_period_fit"],
                **notice_ev,
            },
            "work_mode_alignment": {
                "score": round(mode_score, 2),
                "weight": w["work_mode_alignment"],
                **mode_ev,
            },
            "relocation_willingness": {
                "score": round(reloc_score, 2),
                "weight": w["relocation_willingness"],
                **reloc_ev,
            },
            "verification_status": {
                "score": round(verif_score, 2),
                "weight": w["verification_status"],
                **verif_ev,
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
    def _salary_fit(signals, job) -> tuple[float, dict]:
        """
        Compute salary overlap between the candidate's expected range and
        the job's budget range.

        Overlap score = (overlap_width / union_width) × 100.
        When either range is missing, returns a neutral 50.
        """
        # Job budget — try JD first, then defaults
        job_min = getattr(job, "salary_min_lpa", None) or JOB_DEFAULTS["salary_min_lpa"]
        job_max = getattr(job, "salary_max_lpa", None) or JOB_DEFAULTS["salary_max_lpa"]

        # Candidate expectation
        cand_range = _parse_salary_range(
            signals.expected_salary_range_inr_lpa
        )

        if job_min is None or job_max is None or cand_range is None:
            return 50.0, {
                "note": "Salary data incomplete; defaulted to 50",
                "candidate_range": cand_range,
                "job_range": (job_min, job_max),
            }

        job_min, job_max = float(job_min), float(job_max)
        cand_min, cand_max = cand_range

        # Overlap
        overlap_lo = max(cand_min, job_min)
        overlap_hi = min(cand_max, job_max)
        overlap    = max(0.0, overlap_hi - overlap_lo)

        union_lo = min(cand_min, job_min)
        union_hi = max(cand_max, job_max)
        union    = union_hi - union_lo

        score = (overlap / union * 100.0) if union > 0 else 100.0

        return score, {
            "candidate_range_lpa": list(cand_range),
            "job_range_lpa": [job_min, job_max],
            "overlap_lpa": round(overlap, 2),
            "union_lpa": round(union, 2),
        }

    @staticmethod
    def _notice_period_fit(signals, job) -> tuple[float, dict]:
        """
        Score the candidate's notice period against the job's tolerance.

        - ≤ ideal_max_days   → 100
        - ideal_max < d ≤ acceptable_days → linear decay 100 → 60
        - acceptable < d ≤ maximum_days   → linear decay 60 → 20
        - > maximum_days → 20 (minimum)
        """
        ideal    = RECRUITER_NOTICE["ideal_max_days"]
        accept   = RECRUITER_NOTICE["acceptable_days"]
        maximum  = RECRUITER_NOTICE["maximum_days"]

        # Job override (if explicitly set on the JD object)
        job_max = getattr(job, "max_notice_period_days", None) \
                  or JOB_DEFAULTS["max_notice_period_days"]

        notice = signals.notice_period_days

        if notice is None:
            return 50.0, {
                "notice_period_days": None,
                "note": "No notice period data; defaulted to 50",
            }

        notice = int(notice)

        if notice <= ideal:
            score = 100.0
        elif notice <= accept:
            frac  = (notice - ideal) / (accept - ideal)
            score = 100.0 - frac * 40.0
        elif notice <= maximum:
            frac  = (notice - accept) / (maximum - accept)
            score = 60.0 - frac * 40.0
        else:
            score = 20.0

        return score, {
            "notice_period_days": notice,
            "job_max_days": job_max,
            "exceeds_job_max": notice > job_max,
            "ideal_threshold": ideal,
            "acceptable_threshold": accept,
            "maximum_threshold": maximum,
        }

    @staticmethod
    def _work_mode_alignment(signals, job) -> tuple[float, dict]:
        """
        Use the compatibility matrix to score how well the candidate's
        preferred work mode aligns with the job's requirement.
        """
        cand_mode = _normalise_work_mode(signals.preferred_work_mode)
        job_mode  = _normalise_work_mode(
            getattr(job, "preferred_work_mode", None)
            or JOB_DEFAULTS["preferred_work_mode"]
        )

        # No preference specified on either side — full score
        if job_mode is None:
            return 100.0, {
                "candidate_mode": cand_mode,
                "job_mode": None,
                "note": "No job work-mode requirement; full score",
            }

        if cand_mode is None:
            return 60.0, {
                "candidate_mode": None,
                "job_mode": job_mode,
                "note": "Candidate mode unknown; defaulted to 60",
            }

        score = (
            _WORK_MODE_COMPAT
            .get(cand_mode, {})
            .get(job_mode, 50.0)
        )

        return score, {
            "candidate_mode": cand_mode,
            "job_mode": job_mode,
            "compatibility_used": f"{cand_mode} vs {job_mode}",
        }

    @staticmethod
    def _relocation_fit(signals, job) -> tuple[float, dict]:
        """
        Score based on whether the candidate is willing to relocate and
        whether the job requires it.

        - Job requires relocation + candidate willing   → 100
        - Job requires relocation + candidate unwilling → 0
        - Job doesn't require relocation               → 100 (irrelevant)
        - Candidate willing but job doesn't need it    → 100 (neutral good)
        """
        relocation_required: bool = (
            getattr(job, "relocation_required", None)
            or JOB_DEFAULTS["relocation_required"]
        )
        willing: bool | None = signals.willing_to_relocate

        if not relocation_required:
            return 100.0, {
                "relocation_required": False,
                "candidate_willing": willing,
                "note": "Relocation not required; full score",
            }

        # Relocation IS required
        if willing is True:
            score = 100.0
        elif willing is False:
            score = 0.0
        else:
            score = 50.0   # Unknown — benefit of the doubt

        return score, {
            "relocation_required": True,
            "candidate_willing": willing,
        }

    @staticmethod
    def _verification_status(signals) -> tuple[float, dict]:
        """
        Score based on the number of verification checks passed.
        Each check (email, phone, LinkedIn) contributes equally.
        """
        checks = {
            "verified_email":    signals.verified_email,
            "verified_phone":    signals.verified_phone,
            "linkedin_connected": signals.linkedin_connected,
        }

        total   = len(checks)
        passed  = sum(1 for v in checks.values() if v is True)
        score   = (passed / total) * 100.0 if total else 0.0

        return score, {
            "checks": checks,
            "passed": passed,
            "total": total,
        }

    # ====================================================================
    # Reason builder
    # ====================================================================

    @staticmethod
    def _build_reason(
        salary: float,
        notice: float,
        mode: float,
        reloc: float,
        verif: float,
        signals,
    ) -> str:
        parts = []

        if salary >= 70:
            parts.append("salary expectations aligned")
        elif salary >= 40:
            parts.append("partial salary overlap")
        else:
            parts.append("salary mismatch")

        if notice >= 80:
            parts.append(f"notice period acceptable ({signals.notice_period_days}d)")
        elif notice < 40:
            parts.append(f"long notice period ({signals.notice_period_days}d)")

        mode_label = _normalise_work_mode(signals.preferred_work_mode) or "unknown"
        if mode >= 80:
            parts.append(f"work mode compatible ({mode_label})")
        elif mode < 40:
            parts.append(f"work mode conflict ({mode_label})")

        if reloc == 0.0:
            parts.append("unwilling to relocate (required)")

        verif_n = int(round(verif / 100 * 3))
        parts.append(f"{verif_n}/3 verifications passed")

        return "Recruiter signals: " + "; ".join(parts) + "."
