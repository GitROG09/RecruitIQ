"""
RecruitIQ — AI-Powered Candidate Ranking System
================================================
Entry point for the full ranking pipeline.

Pipeline:
  DataLoader → CandidateFactory → CandidateAnalyzer
  → SemanticMatcher.precompute_candidate_embedding (batch)
  → JobFactory → HybridMatcher (per candidate)
  → RankingEngine → OutputWriter
"""

from __future__ import annotations
import sys, io

# Ensure the console can render the full output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.loader import DataLoader
from factories.candidate_factory import CandidateFactory
from factories.job_factory import JobFactory
from analyzers.candidate_analyzer import CandidateAnalyzer
from matching.experience_matcher import ExperienceMatcher
from matching.skill_matcher import SkillMatcher
from matching.semantic_matcher import SemanticMatcher
from matching.matcher import HybridMatcher
from knowledge_engine.candidate_builder import CandidateKnowledgeBuilder
from knowledge_engine.job_builder import JobKnowledgeBuilder
from core.ranking_engine import RankingEngine
from core.output_writer import OutputWriter


# ==========================================================================
# Job Description
# (In production this would be read from a file or API request)
# ==========================================================================

JD_TEXT = """
Looking for an AI Engineer with 5-9 years of experience in
Python, Machine Learning, Retrieval, Vector Database,
Docker and AWS.

Strong communication and ownership required.
"""


def _section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def _subsection(title: str) -> None:
    print(f"\n{title}")
    print("-" * 70)


# ==========================================================================
# Main pipeline
# ==========================================================================

def main() -> None:

    print("=" * 70)
    print("  RecruitIQ — AI Candidate Ranking System")
    print("=" * 70)

    # ======================================================================
    # Step 1 — Load candidate dataset
    # ======================================================================

    _section("STEP 1 — LOADING CANDIDATES")

    loader = DataLoader()
    raw_candidates = loader.load_json("sample_candidates.json")

    candidates = [
        CandidateFactory.create(raw)
        for raw in raw_candidates
    ]

    print(f"\n  [OK] Loaded {len(candidates)} candidate(s)")

    # ======================================================================
    # Step 2 — Parse Job Description
    # ======================================================================

    _section("STEP 2 — JOB DESCRIPTION INTELLIGENCE")

    job = JobFactory.create(JD_TEXT)

    print(f"\n  Role            : {job.role}")
    print(f"  Experience      : {job.experience_min}–{job.experience_max} years")
    print(f"  Required Skills : {len(job.required_skills)}")
    for skill in job.required_skills:
        print(f"    - {skill}")
    print(f"  Behaviour Traits: {len(job.behaviour_traits)}")
    for trait in job.behaviour_traits:
        print(f"    - {trait}")

    # ======================================================================
    # Step 3 — Diagnostic snapshot of first candidate
    # ======================================================================

    _section("STEP 3 — FIRST CANDIDATE DIAGNOSTIC")

    first = candidates[0]
    analyzer = CandidateAnalyzer(first)
    fv = analyzer.build_feature_vector()

    print(f"\n  Name              : {first.profile.anonymized_name}")
    print(f"  Current Role      : {first.profile.current_title}")
    print(f"  Current Company   : {first.profile.current_company}")

    _subsection("Feature Vector")
    print(f"  Experience             : {fv.experience}")
    print(f"  Companies              : {fv.companies}")
    print(f"  Average Tenure         : {fv.average_tenure} months")
    print(f"  Longest Tenure         : {fv.longest_tenure} months")
    print(f"  Total Skills           : {fv.total_skills}")
    print(f"  Advanced Skills        : {fv.advanced_skills}")
    print(f"  Avg Skill Duration     : {fv.average_skill_duration} months")
    print(f"  Total Endorsements     : {fv.total_endorsements}")
    print(f"  GitHub Activity Score  : {fv.github_activity_score}")

    _subsection("Experience Match (first candidate)")
    exp_result = ExperienceMatcher.score(fv.experience, job.experience_min, job.experience_max)
    print(f"  Score  : {exp_result.score:.2f}")
    print(f"  Reason : {exp_result.reason}")

    _subsection("Skill Match (first candidate)")
    skill_result = SkillMatcher.score(first, job)
    print(f"  Score          : {skill_result.score:.2f}")
    print(f"  Matched Skills : {skill_result.matched_skills}")
    print(f"  Missing Skills : {skill_result.missing_skills}")

    _subsection("Knowledge Documents (first candidate)")
    cand_doc = CandidateKnowledgeBuilder.build(first)
    job_doc  = JobKnowledgeBuilder.build(job)
    print(f"\n  Candidate document ({len(cand_doc)} chars) — preview:")
    print(f"  {cand_doc[:300].strip()}")
    print(f"\n  Job document ({len(job_doc)} chars):")
    print(f"  {job_doc.strip()}")

    # ======================================================================
    # Step 4 — Pre-compute candidate embeddings (batch)
    # ======================================================================

    _section("STEP 4 — PRE-COMPUTING CANDIDATE EMBEDDINGS")

    print(f"\n  Model : {SemanticMatcher._model_name}")
    print(f"  Candidates to embed: {len(candidates)}")
    print()

    for i, candidate in enumerate(candidates, start=1):
        SemanticMatcher.precompute_candidate_embedding(candidate)
        print(f"  [{i:>4}/{len(candidates)}] Embedded {candidate.candidate_id}", flush=True)

    print(f"\n  [OK] Cache size: {SemanticMatcher.cache_size()} embeddings")

    # ======================================================================
    # Step 5 — Run HybridMatcher on all candidates
    # ======================================================================

    _section("STEP 5 — HYBRID MATCHING")

    matcher   = HybridMatcher()
    results   = []

    print()
    for i, candidate in enumerate(candidates, start=1):
        fv     = CandidateAnalyzer(candidate).build_feature_vector()
        result = matcher.match(candidate, fv, job)
        results.append(result)
        print(
            f"  [{i:>4}/{len(candidates)}] "
            f"{candidate.candidate_id}  ->  overall={result.overall_score:.2f}",
            flush=True,
        )

    print(f"\n  [OK] Matched {len(results)} candidate(s)")

    # ======================================================================
    # Step 6 — Rank
    # ======================================================================

    _section("STEP 6 — RANKING")

    engine = RankingEngine()
    ranked = engine.rank(results)

    print(f"\n  [OK] Ranked {len(ranked)} candidate(s)")

    # ======================================================================
    # Step 7 — Export outputs
    # ======================================================================

    _section("STEP 7 — EXPORTING OUTPUTS")

    writer = OutputWriter()
    paths  = writer.write(ranked)

    print(f"\n  [OK] CSV  -> {paths['csv']}")
    print(f"  [OK] JSON -> {paths['json']}")

    # ======================================================================
    # Step 8 — Print leaderboard
    # ======================================================================

    _section("STEP 8 — LEADERBOARD")

    OutputWriter.print_summary(ranked, top_n=min(10, len(ranked)))

    # ======================================================================
    # Done
    # ======================================================================

    print(f"\n{'=' * 70}")
    print(f"  [OK] RecruitIQ pipeline complete.")
    print(f"      Ranked {len(ranked)} candidate(s) for: {job.role}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()