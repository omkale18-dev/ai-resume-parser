from __future__ import annotations

import functools
import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from src.text_preprocessor import preprocess_for_embedding, preprocess_for_tfidf
except ImportError:
    def preprocess_for_tfidf(text: str) -> str:
        return text.lower().strip() if text else ""

    def preprocess_for_embedding(text: str) -> str:
        return text.strip() if text else ""

from src.skill_extractor import match_skills_to_requirements

logger = logging.getLogger(__name__)

def tfidf_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0
    if not text1.strip() or not text2.strip():
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = float(similarity_matrix[0][0])
        return float(np.clip(score, 0.0, 1.0))
    except ValueError:
        return 0.0
    except Exception as exc:
        logger.warning("TF-IDF similarity calculation failed: %s", exc)
        return 0.0

@functools.lru_cache(maxsize=4)
def get_sentence_transformer_model(model_name: str = "all-MiniLM-L6-v2") -> object:
    if SentenceTransformer is None:
        raise ImportError(
            "The 'sentence-transformers' package is required for semantic matching."
        )
    return SentenceTransformer(model_name)

def semantic_similarity(
    text1: str,
    text2: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> float:
    if not text1 or not text2:
        return 0.0
    if not text1.strip() or not text2.strip():
        return 0.0

    try:
        model = get_sentence_transformer_model(model_name)
        embeddings = model.encode([text1, text2], convert_to_numpy=True)
        similarity_matrix = cosine_similarity(embeddings[0:1], embeddings[1:2])
        score = float(similarity_matrix[0][0])
        return float(np.clip(score, 0.0, 1.0))
    except Exception as exc:
        logger.warning(
            "Semantic similarity computation with model '%s' failed: %s",
            model_name,
            exc
        )
        return 0.0

def compute_match(
    resume_text: str,
    job_text: str,
    resume_skills: list[str],
    job_skills: list[str],
    use_semantic: bool = True
) -> dict[str, Any]:
    clean_resume_tfidf = preprocess_for_tfidf(resume_text)
    clean_job_tfidf = preprocess_for_tfidf(job_text)

    tfidf_sim = tfidf_similarity(clean_resume_tfidf, clean_job_tfidf)
    tfidf_score = round(tfidf_sim * 100.0, 2)

    skill_result = match_skills_to_requirements(resume_skills, job_skills)
    matched_skills = skill_result.get("matched", [])
    missing_skills = skill_result.get("missing", [])
    additional_skills = skill_result.get("additional", [])
    skill_match_score = round(float(skill_result.get("match_percentage", 0.0)), 2)

    semantic_score: float | None = None
    if use_semantic:
        try:
            clean_resume_emb = preprocess_for_embedding(resume_text)
            clean_job_emb = preprocess_for_embedding(job_text)
            sem_sim = semantic_similarity(clean_resume_emb, clean_job_emb)
            semantic_score = round(sem_sim * 100.0, 2)
        except Exception as exc:
            logger.warning("Semantic scoring unavailable; falling back to lexical scoring: %s", exc)
            semantic_score = None

    if semantic_score is not None:
        raw_overall = (0.3 * tfidf_score) + (0.4 * semantic_score) + (0.3 * skill_match_score)
    else:
        raw_overall = (0.5 * tfidf_score) + (0.5 * skill_match_score)

    overall_score = round(min(100.0, max(0.0, raw_overall)), 2)

    explanation_parts: list[str] = [
        f"Overall match score is {overall_score:.1f}%."
    ]

    if semantic_score is not None:
        explanation_parts.append(
            f"The score reflects TF-IDF keyword overlap ({tfidf_score:.1f}%, weight 30%), "
            f"semantic contextual similarity ({semantic_score:.1f}%, weight 40%), "
            f"and required skill match ({skill_match_score:.1f}%, weight 30%)."
        )
    else:
        explanation_parts.append(
            f"The score reflects TF-IDF keyword overlap ({tfidf_score:.1f}%, weight 50%) "
            f"and required skill match ({skill_match_score:.1f}%, weight 50%)."
        )

    total_requirements = len(matched_skills) + len(missing_skills)
    if total_requirements > 0:
        explanation_parts.append(
            f"Candidate satisfies {len(matched_skills)} of {total_requirements} required skill(s)."
        )

    if matched_skills:
        matched_preview = ", ".join(matched_skills[:6])
        if len(matched_skills) > 6:
            matched_preview += f" (+{len(matched_skills) - 6} more)"
        explanation_parts.append(f"Confirmed skills: {matched_preview}.")

    if missing_skills:
        missing_preview = ", ".join(missing_skills[:6])
        if len(missing_skills) > 6:
            missing_preview += f" (+{len(missing_skills) - 6} more)"
        explanation_parts.append(f"Gaps identified: {missing_preview}.")
    else:
        explanation_parts.append("Candidate covers all explicitly required skills.")

    explanation = " ".join(explanation_parts)

    return {
        "overall_score": overall_score,
        "tfidf_score": tfidf_score,
        "semantic_score": semantic_score,
        "skill_match_score": skill_match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "additional_skills": additional_skills,
        "explanation": explanation,
    }
