from __future__ import annotations

from models.match_result import MatchResult


class RankingEngine:
    """
    Sorts a list of ``MatchResult`` objects by ``overall_score``
    (descending) and assigns a 1-based rank to each.

    Responsibilities
    ----------------
    - Rank assignment (stable sort preserves insertion order on ties)
    - Tie-breaking via a configurable secondary key
    - Returns a new sorted list; the originals are not mutated

    Usage
    -----
    ::

        engine = RankingEngine()
        ranked = engine.rank(match_results)
        # ranked[0].rank == 1  (highest overall_score)
    """

    def __init__(self, tie_breaker: str = "semantic_score") -> None:
        """
        Parameters
        ----------
        tie_breaker : str
            Attribute name on ``MatchResult`` used as a secondary sort key
            when two candidates share the same ``overall_score``.
            Defaults to ``"semantic_score"`` — the most holistic signal.
        """
        self.tie_breaker = tie_breaker

    def rank(self, results: list[MatchResult]) -> list[RankedResult]:
        """
        Sort and rank a list of match results.

        Parameters
        ----------
        results : list[MatchResult]
            Unordered match results from ``HybridMatcher``.

        Returns
        -------
        list[RankedResult]
            Sorted list, highest score first. Each item carries the
            original ``MatchResult`` plus a ``rank`` integer and a
            ``percentile`` float.
        """
        if not results:
            return []

        sorted_results = sorted(
            results,
            key=lambda r: (
                r.overall_score,
                getattr(r, self.tie_breaker, 0.0),
            ),
            reverse=True,
        )

        total = len(sorted_results)

        ranked: list[RankedResult] = []

        for position, result in enumerate(sorted_results, start=1):
            percentile = round(
                (total - position) / total * 100.0, 1
            )
            ranked.append(
                RankedResult(
                    result=result,
                    rank=position,
                    percentile=percentile,
                )
            )

        return ranked

    # ------------------------------------------------------------------
    # Convenience accessor
    # ------------------------------------------------------------------

    @staticmethod
    def top_n(
        ranked: list["RankedResult"],
        n: int,
    ) -> list["RankedResult"]:
        """Return the top-N ranked results."""
        return ranked[:n]


class RankedResult:
    """
    Wraps a ``MatchResult`` with ranking metadata.

    Attributes
    ----------
    result : MatchResult
        The underlying match result with all scores and reasoning.
    rank : int
        1-based rank (1 = best match).
    percentile : float
        Percentage of candidates this result outscores, e.g. 95.0 means
        the candidate is in the top 5 %.
    """

    def __init__(
        self,
        result: MatchResult,
        rank: int,
        percentile: float,
    ) -> None:
        self.result = result
        self.rank = rank
        self.percentile = percentile

    def to_dict(self) -> dict:
        """
        Flat serialisation for CSV output.

        Merges rank + percentile into the result's own ``to_dict()`` output.
        """
        d = self.result.to_dict()
        d["rank"] = self.rank
        d["percentile"] = self.percentile
        return d

    def __repr__(self) -> str:
        return (
            f"RankedResult("
            f"rank={self.rank}, "
            f"candidate_id={self.result.candidate_id!r}, "
            f"overall={self.result.overall_score:.2f})"
        )
