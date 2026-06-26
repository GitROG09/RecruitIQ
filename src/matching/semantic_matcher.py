from __future__ import annotations

import numpy as np
from typing import Any

from models.match_score import MatchScore
from config.scoring import SEMANTIC_CONFIG
from knowledge_engine.candidate_builder import CandidateKnowledgeBuilder
from knowledge_engine.job_builder import JobKnowledgeBuilder


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1-D numpy vectors.
    Returns a value in [-1.0, 1.0]; sentence-transformer embeddings
    are unit-normalised so the result is typically in [0.0, 1.0].
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class SemanticMatcher:
    """
    Computes semantic similarity between a candidate and a job description
    using sentence-transformer embeddings (``all-MiniLM-L6-v2`` by default).

    Architecture
    ------------
    - **Candidate embeddings** are pre-computed once and stored in an
      in-memory class-level cache keyed by ``candidate_id``.
      Call :meth:`precompute_candidate_embedding` for each candidate before
      ranking begins.
    - **Job embeddings** are computed fresh at ranking time (one per job).
    - Cosine similarity is computed in pure NumPy — no external API calls.

    The model is loaded lazily on first use and kept as a class-level
    singleton to avoid reloading between candidates.
    """

    # ------------------------------------------------------------------
    # Class-level state (shared across all instances)
    # ------------------------------------------------------------------

    _model = None                          # lazy singleton
    _embedding_cache: dict[str, np.ndarray] = {}   # candidate_id → embedding
    _model_name: str = str(SEMANTIC_CONFIG["model_name"])

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    @classmethod
    def _get_model(cls):
        """
        Lazily load the sentence-transformer model on first call.
        Subsequent calls return the cached instance immediately.
        """
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required for SemanticMatcher. "
                    "Install it with: pip install sentence-transformers"
                ) from exc

            cache_dir = SEMANTIC_CONFIG.get("cache_dir")
            cls._model = SentenceTransformer(
                cls._model_name,
                cache_folder=cache_dir,
            )

        return cls._model

    # ------------------------------------------------------------------
    # Embedding cache
    # ------------------------------------------------------------------

    @classmethod
    def precompute_candidate_embedding(cls, candidate) -> np.ndarray:
        """
        Build the candidate's knowledge document, generate its embedding,
        and store it in the class-level cache.

        Call this **once per candidate** before ranking begins so that
        subsequent :meth:`score` calls are fast (no re-embedding).

        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.

        Returns
        -------
        np.ndarray
            The embedding vector (cached for future use).
        """
        cid = candidate.candidate_id

        if cid not in cls._embedding_cache:
            doc = CandidateKnowledgeBuilder.build(candidate)
            model = cls._get_model()
            embedding = model.encode(doc, convert_to_numpy=True)
            cls._embedding_cache[cid] = embedding

        return cls._embedding_cache[cid]

    @classmethod
    def clear_cache(cls) -> None:
        """Evict all cached candidate embeddings (e.g., between jobs)."""
        cls._embedding_cache.clear()

    @classmethod
    def cache_size(cls) -> int:
        """Return the number of candidates currently in the cache."""
        return len(cls._embedding_cache)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    @classmethod
    def score(cls, candidate, job) -> MatchScore:
        """
        Compute semantic similarity between the candidate and the job.

        The candidate embedding is retrieved from the cache (or computed
        and cached on first call). The job embedding is generated fresh.

        Parameters
        ----------
        candidate : Candidate
            The candidate domain object.
        job : JobDescription
            The parsed job description.

        Returns
        -------
        MatchScore
            score    – cosine similarity scaled to [0, 100]
            reason   – one-line human-readable interpretation
            evidence – raw similarity, document lengths, model name
        """
        # ---- Candidate embedding (from cache) -------------------------
        cand_embedding = cls.precompute_candidate_embedding(candidate)
        cache_hit = candidate.candidate_id in cls._embedding_cache

        # ---- Job embedding (computed fresh) ---------------------------
        job_doc = JobKnowledgeBuilder.build(job)
        model   = cls._get_model()
        job_embedding = model.encode(job_doc, convert_to_numpy=True)

        # ---- Cosine similarity ----------------------------------------
        raw_similarity = _cosine_similarity(cand_embedding, job_embedding)

        threshold = float(SEMANTIC_CONFIG.get("similarity_threshold", 0.0))
        clamped   = max(threshold, raw_similarity)
        score     = round(clamped * 100.0, 2)

        # ---- Candidate document length (for evidence) -----------------
        cand_doc = CandidateKnowledgeBuilder.build(candidate)

        reason = cls._build_reason(score, raw_similarity)

        evidence: dict[str, Any] = {
            "model": cls._model_name,
            "raw_cosine_similarity": round(raw_similarity, 6),
            "similarity_threshold": threshold,
            "cache_hit": cache_hit,
            "candidate_doc_length_chars": len(cand_doc),
            "job_doc_length_chars": len(job_doc),
        }

        return MatchScore(
            score=score,
            reason=reason,
            evidence=evidence,
        )

    # ------------------------------------------------------------------
    # Reason builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reason(score: float, similarity: float) -> str:
        if score >= 80:
            label = "very strong"
        elif score >= 60:
            label = "strong"
        elif score >= 40:
            label = "moderate"
        elif score >= 20:
            label = "weak"
        else:
            label = "very weak"

        return (
            f"Semantic similarity is {label} "
            f"(cosine={similarity:.4f}, score={score:.1f}/100)."
        )
