from __future__ import annotations

from datetime import date, datetime
from typing import Any

from models.match_score import MatchScore
from config.scoring import BEHAVIOUR_WEIGHTS, BEHAVIOUR_RECENCY
from config.job_config import JOB_DEFAULTS


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str | None) -> date | None:
    """
    Parse a date string in common formats (YYYY-MM-DD, YYYY-MM, YYYY).
    Returns None if the value is absent or unparseable.
    """
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _days_since(date_value: str | None) -> int | None:
    """
    Return the number of calendar days since ``date_value``.
    Returns None if the date cannot be parsed.
    """
    parsed = _parse_date(date_value)
    if parsed is None:
        return None
    return (date.today() - parsed).days


class BehaviourMatcher:
    """
    Evaluates a candidate's behavioural and platform engagement signals
    using data from ``RedrobSignals``.

    Six weighted signals:

    1. Profile Completeness    (20 %) — how complete is the candidate profile
    2. Activity Recency        (20 %) — how recently was the profile active
    3. Open-to-Work Flag       (10 %) — explicit availability signal
    4. Assessment Scores       (20 %) — Redrob skill assessment performance
    5. Interview / Offer Rates (15 %) — completion and acceptance history
    6. GitHub Activity         (15 %) — external coding contribution signal

    All sub-weights are read from ``config.scoring.BEHAVIOUR_WEIGHTS``.
    """

    @staticmethod
    def score(candidate, job=None) -> MatchScore:
        """
        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.
        job : JobDescription | None
            Optional — used to read ``min_profile_completeness`` if set.

        Returns
        -------
        MatchScore
            score    – weighted composite [0, 100]
            reason   – one-line human-readable summary
            evidence – per-signal scores and structured details
        """
        signals = candidate.redrob_signals

        # ----------------------------------------------------------------
        # Signal 1 — Profile Completeness
        # ----------------------------------------------------------------
        completeness_score, completeness_ev = BehaviourMatcher._profile_completeness(
            signals, job
        )

        # ----------------------------------------------------------------
        # Signal 2 — Activity Recency
        # ----------------------------------------------------------------
        recency_score, recency_ev = BehaviourMatcher._activity_recency(signals)

        # ----------------------------------------------------------------
        # Signal 3 — Open-to-Work Flag
        # ----------------------------------------------------------------
        otw_score, otw_ev = BehaviourMatcher._open_to_work(signals)

        # ----------------------------------------------------------------
        # Signal 4 — Assessment Scores
        # ----------------------------------------------------------------
        assessment_score, assessment_ev = BehaviourMatcher._assessment_scores(
            signals
        )

        # ----------------------------------------------------------------
        # Signal 5 — Interview / Offer Completion Rates
        # ----------------------------------------------------------------
        ir_score, ir_ev = BehaviourMatcher._interview_offer_rates(signals)

        # ----------------------------------------------------------------
        # Signal 6 — GitHub Activity
        # ----------------------------------------------------------------
        github_score, github_ev = BehaviourMatcher._github_activity(signals)

        # ----------------------------------------------------------------
        # Weighted composite
        # ----------------------------------------------------------------
        w = BEHAVIOUR_WEIGHTS
        composite = (
            completeness_score * w["profile_completeness"]
            + recency_score    * w["activity_recency"]
            + otw_score        * w["open_to_work"]
            + assessment_score * w["assessment_scores"]
            + ir_score         * w["interview_offer_rates"]
            + github_score     * w["github_activity"]
        )

        # ----------------------------------------------------------------
        # Reason + evidence
        # ----------------------------------------------------------------
        reason = BehaviourMatcher._build_reason(
            completeness_score, recency_score, otw_score,
            assessment_score, ir_score, github_score,
        )

        evidence: dict[str, Any] = {
            "profile_completeness": {
                "score": round(completeness_score, 2),
                "weight": w["profile_completeness"],
                **completeness_ev,
            },
            "activity_recency": {
                "score": round(recency_score, 2),
                "weight": w["activity_recency"],
                **recency_ev,
            },
            "open_to_work": {
                "score": round(otw_score, 2),
                "weight": w["open_to_work"],
                **otw_ev,
            },
            "assessment_scores": {
                "score": round(assessment_score, 2),
                "weight": w["assessment_scores"],
                **assessment_ev,
            },
            "interview_offer_rates": {
                "score": round(ir_score, 2),
                "weight": w["interview_offer_rates"],
                **ir_ev,
            },
            "github_activity": {
                "score": round(github_score, 2),
                "weight": w["github_activity"],
                **github_ev,
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
    def _profile_completeness(
        signals, job
    ) -> tuple[float, dict]:
        """
        Score based on the platform-reported profile completeness value.
        Applies a soft penalty if the score is below the JD's minimum
        threshold (read from job_config defaults if not set on the JD).
        """
        raw = signals.profile_completeness_score

        if raw is None:
            return 40.0, {"raw_completeness": None, "note": "No data; defaulted to 40"}

        raw = float(raw)
        min_threshold = JOB_DEFAULTS["min_profile_completeness"]

        # Normalise: treat the raw value as already [0–100]
        score = min(100.0, max(0.0, raw))

        below_threshold = raw < min_threshold

        return score, {
            "raw_completeness": raw,
            "min_threshold": min_threshold,
            "below_threshold": below_threshold,
        }

    @staticmethod
    def _activity_recency(signals) -> tuple[float, dict]:
        """
        Score recency of profile activity using ``last_active_date``.

        - ≤ fresh_days   → 100
        - fresh_days < d ≤ stale_days  → linear decay 100 → 50
        - stale_days < d ≤ inactive_days → linear decay 50 → 20
        - > inactive_days → 20 (minimum)
        """
        fresh    = BEHAVIOUR_RECENCY["fresh_days"]
        stale    = BEHAVIOUR_RECENCY["stale_days"]
        inactive = BEHAVIOUR_RECENCY["inactive_days"]

        days = _days_since(signals.last_active_date)

        if days is None:
            return 40.0, {
                "last_active_date": signals.last_active_date,
                "days_since_active": None,
                "note": "No date available; defaulted to 40",
            }

        if days <= fresh:
            score = 100.0
        elif days <= stale:
            frac  = (days - fresh) / (stale - fresh)
            score = 100.0 - frac * 50.0
        elif days <= inactive:
            frac  = (days - stale) / (inactive - stale)
            score = 50.0 - frac * 30.0
        else:
            score = 20.0

        return score, {
            "last_active_date": str(signals.last_active_date),
            "days_since_active": days,
            "fresh_threshold_days": fresh,
            "stale_threshold_days": stale,
            "inactive_threshold_days": inactive,
        }

    @staticmethod
    def _open_to_work(signals) -> tuple[float, dict]:
        """
        Binary signal — full score if the candidate has flagged
        themselves as open to work, partial if not set, zero if hidden.
        """
        flag = signals.open_to_work_flag

        if flag is True:
            score = 100.0
            label = "active"
        elif flag is False:
            score = 20.0
            label = "not_open"
        else:
            score = 50.0   # Unknown — neutral
            label = "unknown"

        return score, {"open_to_work_flag": flag, "status": label}

    @staticmethod
    def _assessment_scores(signals) -> tuple[float, dict]:
        """
        Compute average across all completed Redrob skill assessments.
        Returns 50 (neutral) when no assessments exist.
        """
        assessments: dict | None = signals.skill_assessment_scores

        if not assessments:
            return 50.0, {
                "assessments": {},
                "count": 0,
                "note": "No assessments taken; defaulted to 50",
            }

        scores = [
            float(v)
            for v in assessments.values()
            if v is not None
        ]

        if not scores:
            return 50.0, {"assessments": assessments, "count": 0}

        avg = sum(scores) / len(scores)

        return min(100.0, avg), {
            "assessments": assessments,
            "count": len(scores),
            "average_raw": round(avg, 2),
        }

    @staticmethod
    def _interview_offer_rates(signals) -> tuple[float, dict]:
        """
        Equally weight interview_completion_rate and offer_acceptance_rate.
        Both are expected as floats in [0.0, 1.0] or [0, 100].
        Missing values default to neutral (0.5 / 50).
        """

        def _normalise(val) -> float:
            if val is None:
                return 50.0
            v = float(val)
            return v * 100.0 if v <= 1.0 else min(100.0, v)

        ir = _normalise(signals.interview_completion_rate)
        oa = _normalise(signals.offer_acceptance_rate)
        avg = (ir + oa) / 2.0

        return avg, {
            "interview_completion_rate_raw": signals.interview_completion_rate,
            "offer_acceptance_rate_raw": signals.offer_acceptance_rate,
            "interview_score": round(ir, 2),
            "offer_score": round(oa, 2),
        }

    @staticmethod
    def _github_activity(signals) -> tuple[float, dict]:
        """
        Map the Redrob github_activity_score (expected [0–100]) directly.
        Returns 30 (below average) when absent.
        """
        raw = signals.github_activity_score

        if raw is None:
            return 30.0, {
                "github_activity_score": None,
                "note": "No GitHub data; defaulted to 30",
            }

        score = min(100.0, max(0.0, float(raw)))

        return score, {"github_activity_score": raw}

    # ====================================================================
    # Reason builder
    # ====================================================================

    @staticmethod
    def _build_reason(
        completeness: float,
        recency: float,
        otw: float,
        assessment: float,
        ir: float,
        github: float,
    ) -> str:
        parts = []

        parts.append(
            f"profile {int(completeness)}% complete"
        )

        if recency >= 80:
            parts.append("recently active")
        elif recency >= 40:
            parts.append("moderately active")
        else:
            parts.append("inactive profile")

        if otw >= 80:
            parts.append("open to work")

        if assessment >= 70:
            parts.append(f"strong assessments ({int(assessment)}/100)")
        elif assessment > 50:
            parts.append(f"average assessments ({int(assessment)}/100)")

        if github >= 60:
            parts.append("active GitHub contributions")

        if ir >= 75:
            parts.append("high interview/offer completion")
        elif ir < 40:
            parts.append("low interview/offer completion")

        return "Behaviour signals: " + "; ".join(parts) + "."
