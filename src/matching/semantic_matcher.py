from __future__ import annotations

import hashlib

import numpy as np

from typing import Any

from models.match_score import MatchScore

from config.scoring import SEMANTIC_CONFIG

from knowledge_engine.candidate_builder import (
    CandidateKnowledgeBuilder,
)

from knowledge_engine.job_builder import (
    JobKnowledgeBuilder,
)


def _content_key(text: str) -> str:
    """
    Stable cache key derived from document *content*, not from the
    caller-supplied candidate_id.

    Why: SemanticMatcher's caches are process-level (class attributes),
    and on a deployed Streamlit app a single process serves every user's
    session concurrently. Two different users can independently upload
    candidates that happen to share the same candidate_id (e.g. both
    named "CAND_001"). Keying on candidate_id alone would let User B
    silently receive User A's cached embedding for a completely
    different person. Keying on a hash of the actual document text
    avoids that collision, and as a bonus de-duplicates identical
    documents across runs.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cosine_similarity(
    a: np.ndarray,
    b: np.ndarray,
) -> float:
    """
    Compute cosine similarity between two vectors.
    """

    norm_a = np.linalg.norm(a)

    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(
        np.dot(a, b) / (norm_a * norm_b)
    )


class SemanticMatcher:
    """
    Semantic similarity engine using SentenceTransformers.

    Improvements over the original version
    --------------------------------------

    ✔ Cached candidate embeddings

    ✔ Lazy model loading

    ✔ Better score calibration

    ✔ Confidence estimation

    ✔ Better recruiter explanations

    ✔ Rich evidence for Explainability Engine

    ✔ ATS-like scoring behaviour
    """

    # ---------------------------------------------------------
    # Shared state
    # ---------------------------------------------------------

    _model = None

    _embedding_cache: dict[str, np.ndarray] = {}

    _candidate_doc_cache: dict[str, str] = {}

    # candidate_id -> content-hash key, valid only within the current
    # process's lifetime (not persisted, just an internal lookup aid)
    _id_to_key: dict[str, str] = {}

    _model_name = str(
        SEMANTIC_CONFIG["model_name"]
    )

    # ---------------------------------------------------------
    # Calibration values
    # ---------------------------------------------------------

    HIGH_CONFIDENCE = 0.72

    MEDIUM_CONFIDENCE = 0.60

    LOW_CONFIDENCE = 0.45

    # ---------------------------------------------------------
    # Model Loading
    # ---------------------------------------------------------

    @classmethod
    def _get_model(cls):

        if cls._model is None:

            try:

                from sentence_transformers import (
                    SentenceTransformer
                )

            except ImportError as exc:

                raise ImportError(

                    "sentence-transformers is required.\n"
                    "Install using:\n"
                    "pip install sentence-transformers"

                ) from exc

            cls._model = SentenceTransformer(

                cls._model_name,

                cache_folder=SEMANTIC_CONFIG.get(
                    "cache_dir"
                )

            )

        return cls._model

    # ---------------------------------------------------------
    # Candidate Embedding Cache
    # ---------------------------------------------------------

    @classmethod
    def precompute_candidate_embedding(
        cls,
        candidate,
    ) -> np.ndarray:
        """
        Build candidate document once and cache both the
        document and embedding, keyed by a hash of the document's
        content (see ``_content_key``) rather than candidate_id.

        This method should be called before ranking begins.
        """

        candidate_id = candidate.candidate_id

        # ---------------------------------------------
        # Build candidate knowledge document
        # (cheap: string construction, not the model call)
        # ---------------------------------------------

        candidate_document = CandidateKnowledgeBuilder.build(
            candidate
        )

        cache_key = _content_key(candidate_document)

        cls._candidate_doc_cache[candidate_id] = candidate_document
        cls._id_to_key[candidate_id] = cache_key

        # Already cached under this content hash
        if cache_key in cls._embedding_cache:
            return cls._embedding_cache[cache_key]

        # ---------------------------------------------
        # Generate embedding
        # ---------------------------------------------

        model = cls._get_model()

        embedding = model.encode(

            candidate_document,

            convert_to_numpy=True,

            normalize_embeddings=True

        )

        cls._embedding_cache[cache_key] = embedding

        return embedding

    # ---------------------------------------------------------
    # Retrieve Cached Candidate Document
    # ---------------------------------------------------------

    @classmethod
    def _get_candidate_document(
        cls,
        candidate,
    ) -> str:

        candidate_id = candidate.candidate_id

        if candidate_id not in cls._candidate_doc_cache:

            cls.precompute_candidate_embedding(
                candidate
            )

        return cls._candidate_doc_cache[
            candidate_id
        ]

    # ---------------------------------------------------------
    # Cache Utilities
    # ---------------------------------------------------------

    @classmethod
    def clear_cache(cls):
        """
        Clears every cached object.
        """

        cls._embedding_cache.clear()

        cls._candidate_doc_cache.clear()

        cls._id_to_key.clear()

    @classmethod
    def cache_size(cls):

        return len(
            cls._embedding_cache
        )

    @classmethod
    def cache_info(cls) -> dict:
        """
        Useful for debugging and dashboard statistics.
        """

        return {

            "model_loaded": cls._model is not None,

            "embedding_cache_size":
                len(cls._embedding_cache),

            "document_cache_size":
                len(cls._candidate_doc_cache),

            "model_name":
                cls._model_name,

        }
    # ---------------------------------------------------------
    # Semantic Scoring
    # ---------------------------------------------------------

    @classmethod
    def score(
        cls,
        candidate,
        job,
    ) -> MatchScore:
        """
        Compute semantic similarity between candidate and job.

        Returns a calibrated recruiter-style score rather than
        the raw cosine similarity.
        """

        # -------------------------------------------------
        # Candidate Embedding (cached)
        # -------------------------------------------------

        # precompute_candidate_embedding() populates _id_to_key as a
        # side effect, so check cache membership *before* calling it to
        # get an accurate "was this already cached" reading.
        existing_key = cls._id_to_key.get(candidate.candidate_id)
        cache_hit = existing_key is not None and existing_key in cls._embedding_cache

        candidate_embedding = cls.precompute_candidate_embedding(
            candidate
        )

        candidate_document = cls._get_candidate_document(
            candidate
        )

        # -------------------------------------------------
        # Job Document
        # -------------------------------------------------

        job_document = JobKnowledgeBuilder.build(
            job
        )

        model = cls._get_model()

        job_embedding = model.encode(

            job_document,

            convert_to_numpy=True,

            normalize_embeddings=True

        )

        # -------------------------------------------------
        # Raw Cosine Similarity
        # -------------------------------------------------

        cosine = _cosine_similarity(

            candidate_embedding,

            job_embedding

        )

        cosine = max(
            0.0,
            min(1.0, cosine)
        )

        # -------------------------------------------------
        # Recruiter-style Calibration
        # -------------------------------------------------

        score = cls._calibrate_similarity(
            cosine
        )

        # -------------------------------------------------
        # Confidence
        # -------------------------------------------------

        confidence = cls._confidence_label(
            cosine
        )

        # -------------------------------------------------
        # Semantic Band
        # -------------------------------------------------

        if cosine >= 0.75:

            semantic_band = "Excellent"

        elif cosine >= 0.65:

            semantic_band = "Strong"

        elif cosine >= 0.55:

            semantic_band = "Good"

        elif cosine >= 0.45:

            semantic_band = "Average"

        else:

            semantic_band = "Weak"

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        reason = cls._build_reason(

            cosine,

            score,

            confidence,

            semantic_band

        )

        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        evidence = {

            "embedding_model":
                cls._model_name,

            "raw_cosine_similarity":
                round(cosine, 4),

            "calibrated_score":
                score,

            "confidence":
                confidence,

            "semantic_band":
                semantic_band,

            "cache_hit":
                cache_hit,

            "candidate_document_length":
                len(candidate_document),

            "job_document_length":
                len(job_document),

            "embedding_dimension":
                len(candidate_embedding),

        }

        return MatchScore(

            score=score,

            reason=reason,

            evidence=evidence,

        )

    # ---------------------------------------------------------
    # Similarity Calibration
    # ---------------------------------------------------------

    @staticmethod
    def _calibrate_similarity(
        cosine: float,
    ) -> float:
        """
        Convert cosine similarity into a recruiter-friendly score.
        """

        if cosine >= 0.90:
            return 100.0

        elif cosine >= 0.85:
            return 98.0

        elif cosine >= 0.80:
            return 95.0

        elif cosine >= 0.75:
            return 92.0

        elif cosine >= 0.70:
            return 88.0

        elif cosine >= 0.65:
            return 84.0

        elif cosine >= 0.60:
            return 80.0

        elif cosine >= 0.55:
            return 75.0

        elif cosine >= 0.50:
            return 70.0

        elif cosine >= 0.45:
            return 64.0

        elif cosine >= 0.40:
            return 58.0

        elif cosine >= 0.35:
            return 50.0

        elif cosine >= 0.30:
            return 42.0

        return round(cosine * 100, 2)

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    @classmethod
    def _confidence_label(
        cls,
        cosine: float,
    ) -> str:

        if cosine >= cls.HIGH_CONFIDENCE:
            return "Very High"

        elif cosine >= cls.MEDIUM_CONFIDENCE:
            return "High"

        elif cosine >= cls.LOW_CONFIDENCE:
            return "Medium"

        return "Low"

    # ---------------------------------------------------------
    # Reason Builder
    # ---------------------------------------------------------

    @staticmethod
    def _build_reason(
        cosine: float,
        score: float,
        confidence: str,
        semantic_band: str,
    ) -> str:

        if semantic_band == "Excellent":

            summary = (
                "Candidate profile is highly aligned with the job "
                "requirements, technologies and responsibilities."
            )

        elif semantic_band == "Strong":

            summary = (
                "Candidate demonstrates strong semantic alignment with "
                "the role and required technical stack."
            )

        elif semantic_band == "Good":

            summary = (
                "Candidate satisfies a good portion of the semantic "
                "requirements with some noticeable gaps."
            )

        elif semantic_band == "Average":

            summary = (
                "Candidate partially aligns with the job but additional "
                "skills or experience would improve suitability."
            )

        else:

            summary = (
                "Limited semantic alignment detected between candidate "
                "profile and job description."
            )

        return (
            f"{summary} "
            f"Confidence: {confidence}. "
            f"Cosine Similarity: {cosine:.3f}. "
            f"Semantic Score: {score:.1f}/100."
        )
