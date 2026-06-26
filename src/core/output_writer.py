from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import OUTPUT_DIR
from core.ranking_engine import RankedResult


# Column order in the output CSV
_CSV_COLUMNS = [
    "rank",
    "candidate_id",
    "overall_score",
    "percentile",
    "experience_score",
    "skill_score",
    "career_score",
    "behaviour_score",
    "recruiter_score",
    "semantic_score",
    "explanation",
]


class OutputWriter:
    """
    Writes ranked candidate results to disk.

    Produces two artefacts in ``config.settings.OUTPUT_DIR``:

    1. ``ranked_candidates.csv``  — flat CSV with one row per candidate.
    2. ``ranked_candidates_detail.json`` — full JSON including the complete
       per-matcher reasoning and evidence payloads, for debugging and
       the Explainability Engine.

    The output directory is created automatically if it does not exist.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        """
        Parameters
        ----------
        output_dir : Path | None
            Target directory. Defaults to ``OUTPUT_DIR`` from settings.
        """
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, ranked_results: list[RankedResult]) -> dict[str, Path]:
        """
        Serialise ranked results to CSV and JSON.

        Parameters
        ----------
        ranked_results : list[RankedResult]
            Output from ``RankingEngine.rank()``, sorted best-first.

        Returns
        -------
        dict[str, Path]
            ``{"csv": <path>, "json": <path>}`` for downstream logging.
        """
        csv_path  = self._write_csv(ranked_results)
        json_path = self._write_json(ranked_results)

        return {"csv": csv_path, "json": json_path}

    # ------------------------------------------------------------------
    # Private writers
    # ------------------------------------------------------------------

    def _write_csv(self, ranked_results: list[RankedResult]) -> Path:
        """
        Write the flat ranked_candidates.csv.

        Columns: rank, candidate_id, overall_score, percentile,
        experience_score, skill_score, career_score, behaviour_score,
        recruiter_score, semantic_score, explanation.
        """
        path = self.output_dir / "ranked_candidates.csv"

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=_CSV_COLUMNS,
                extrasaction="ignore",
            )
            writer.writeheader()

            for rr in ranked_results:
                row = rr.to_dict()
                # Round all numeric fields to 2 dp for readability
                for col in _CSV_COLUMNS:
                    val = row.get(col)
                    if isinstance(val, float):
                        row[col] = round(val, 2)
                writer.writerow(row)

        return path

    def _write_json(self, ranked_results: list[RankedResult]) -> Path:
        """
        Write ranked_candidates_detail.json with full reasoning payloads.

        Each entry contains:
        - All CSV fields
        - reasoning: list of per-matcher dicts with score, weight,
          weighted_contribution, reason, and evidence
        """
        path = self.output_dir / "ranked_candidates_detail.json"

        records: list[dict[str, Any]] = []

        for rr in ranked_results:
            record = rr.to_dict()
            record["reasoning"] = rr.result.reasoning
            records.append(record)

        payload = {
            "generated_at": datetime.now().isoformat(),
            "total_candidates": len(records),
            "results": records,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

        return path

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------

    @staticmethod
    def print_summary(
        ranked_results: list[RankedResult],
        top_n: int = 10,
    ) -> None:
        """
        Print a formatted leaderboard to stdout.

        Parameters
        ----------
        ranked_results : list[RankedResult]
            Sorted ranked results.
        top_n : int
            How many rows to display. Default 10.
        """
        header = (
            f"{'Rank':<6} {'Candidate':<16} {'Overall':>8} "
            f"{'Exp':>6} {'Skill':>6} {'Career':>7} "
            f"{'Behav':>6} {'Recr':>6} {'Sem':>6} {'%ile':>6}"
        )
        divider = "-" * len(header)

        print("\n" + "=" * len(header))
        print(" RANKED CANDIDATES")
        print("=" * len(header))
        print(header)
        print(divider)

        for rr in ranked_results[:top_n]:
            r = rr.result
            print(
                f"{rr.rank:<6} "
                f"{r.candidate_id:<16} "
                f"{r.overall_score:>8.2f} "
                f"{r.experience_score:>6.1f} "
                f"{r.skill_score:>6.1f} "
                f"{r.career_score:>7.1f} "
                f"{r.behaviour_score:>6.1f} "
                f"{r.recruiter_score:>6.1f} "
                f"{r.semantic_score:>6.1f} "
                f"{rr.percentile:>6.1f}"
            )

        if len(ranked_results) > top_n:
            print(f"  ... and {len(ranked_results) - top_n} more candidates")

        print(divider)
