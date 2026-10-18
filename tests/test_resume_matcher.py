from __future__ import annotations

import json
from typing import Any
import pytest

from src.report_generator import (
    generate_csv_report,
    generate_improvement_suggestions,
    generate_json_report,
)
from src.resume_matcher import (
    compute_match,
    semantic_similarity,
    tfidf_similarity,
)
from src.skill_extractor import match_skills_to_requirements

try:
    import sentence_transformers
    HAS_ST = True
except ImportError:
    HAS_ST = False

def test_tfidf_similarity_identical() -> None:
    text = "Experienced Python developer building REST APIs and microservices with Docker and PostgreSQL."
    score = tfidf_similarity(text, text)

    assert pytest.approx(1.0, abs=1e-3) == score

def test_tfidf_similarity_different() -> None:
    text1 = "Python developer building machine learning models with PyTorch and CUDA."
    text2 = "Pastry chef baking sourdough artisan breads and decorating wedding cakes."
    score = tfidf_similarity(text1, text2)

    assert score < 0.05

def test_tfidf_similarity_empty() -> None:
    sample_text = "Senior Software Engineer"

    assert tfidf_similarity("", sample_text) == 0.0
    assert tfidf_similarity(sample_text, "") == 0.0
    assert tfidf_similarity("", "") == 0.0
    assert tfidf_similarity("   ", "   ") == 0.0
    assert tfidf_similarity("!@#$%^", "!@#$%^") == 0.0

def test_tfidf_similarity_partial_overlap() -> None:
    text1 = "Python backend developer with Django and PostgreSQL database experience"
    text2 = "Python frontend engineer with React and Django framework knowledge"
    score = tfidf_similarity(text1, text2)

    assert 0.1 < score < 0.95

@pytest.mark.skipif(not HAS_ST, reason="sentence-transformers not installed")
def test_semantic_similarity() -> None:
    text1 = "Senior software engineer with extensive backend architecture experience in Python"
    text2 = "Lead programmer specializing in server-side system development using Python"
    score = semantic_similarity(text1, text2)

    assert 0.0 <= score <= 1.0
    assert score > 0.5

    assert semantic_similarity("", text2) == 0.0
    assert semantic_similarity(text1, "") == 0.0

def test_compute_match_without_semantic() -> None:
    resume_text = "Senior Python engineer building cloud backend microservices in AWS."
    job_text = "Looking for a Python engineer with cloud and AWS microservices experience."
    resume_skills = ["Python", "AWS", "Docker", "Git"]
    job_skills = ["Python", "AWS", "Kubernetes"]

    result = compute_match(
        resume_text=resume_text,
        job_text=job_text,
        resume_skills=resume_skills,
        job_skills=job_skills,
        use_semantic=False,
    )

    assert isinstance(result, dict)
    assert result["semantic_score"] is None
    assert 0.0 <= result["overall_score"] <= 100.0
    assert 0.0 <= result["tfidf_score"] <= 100.0
    assert 0.0 <= result["skill_match_score"] <= 100.0

    expected_overall = round(
        0.5 * result["tfidf_score"] + 0.5 * result["skill_match_score"], 2
    )
    assert result["overall_score"] == expected_overall
    assert isinstance(result["explanation"], str)
    assert len(result["explanation"]) > 0

def test_compute_match_score_range() -> None:
    resume_text = "Frontend specialist in React, TypeScript, and modern CSS frameworks."
    job_text = "Seeking React Developer proficient in TypeScript and responsive UI design."
    resume_skills = ["React", "TypeScript", "CSS"]
    job_skills = ["React", "TypeScript", "HTML"]

    result = compute_match(
        resume_text=resume_text,
        job_text=job_text,
        resume_skills=resume_skills,
        job_skills=job_skills,
        use_semantic=False,
    )

    assert 0.0 <= result["overall_score"] <= 100.0
    assert 0.0 <= result["tfidf_score"] <= 100.0
    assert 0.0 <= result["skill_match_score"] <= 100.0

def test_compute_match_skills() -> None:
    resume_text = "Python Developer with Java, Docker, and PostgreSQL skills."
    job_text = "Backend Engineer needing Python, Docker, Kubernetes, and AWS."
    resume_skills = ["Python", "Java", "Docker", "PostgreSQL"]
    job_skills = ["Python", "Docker", "Kubernetes", "AWS"]

    result = compute_match(
        resume_text=resume_text,
        job_text=job_text,
        resume_skills=resume_skills,
        job_skills=job_skills,
        use_semantic=False,
    )

    assert set(result["matched_skills"]) == {"Python", "Docker"}
    assert set(result["missing_skills"]) == {"Kubernetes", "AWS"}
    assert set(result["additional_skills"]) == {"Java", "PostgreSQL"}
    assert result["skill_match_score"] == 50.0

def test_compute_match_empty_skills() -> None:
    result = compute_match(
        resume_text="Experienced professional.",
        job_text="Seeking professional candidate.",
        resume_skills=[],
        job_skills=[],
        use_semantic=False,
    )

    assert result["matched_skills"] == []
    assert result["missing_skills"] == []
    assert result["additional_skills"] == []
    assert result["skill_match_score"] == 100.0
    assert 0.0 <= result["overall_score"] <= 100.0

def test_skill_matching_all_matched() -> None:
    candidate_skills = ["Python", "Django", "PostgreSQL", "Docker", "Git"]
    required_skills = ["Python", "Docker", "Git"]

    result = match_skills_to_requirements(candidate_skills, required_skills)

    assert set(result["matched"]) == {"Python", "Docker", "Git"}
    assert result["missing"] == []
    assert set(result["additional"]) == {"Django", "PostgreSQL"}
    assert result["match_percentage"] == 100.0

def test_skill_matching_none_matched() -> None:
    candidate_skills = ["Java", "Spring Boot", "Oracle"]
    required_skills = ["Python", "Django", "PostgreSQL"]

    result = match_skills_to_requirements(candidate_skills, required_skills)

    assert result["matched"] == []
    assert set(result["missing"]) == {"Python", "Django", "PostgreSQL"}
    assert set(result["additional"]) == {"Java", "Spring Boot", "Oracle"}
    assert result["match_percentage"] == 0.0

def test_skill_matching_partial() -> None:
    candidate_skills = ["python", "react", "c++"]
    required_skills = ["Python", "Angular", "Vue.js", "C++"]

    result = match_skills_to_requirements(candidate_skills, required_skills)

    assert set(result["matched"]) == {"Python", "C++"}
    assert set(result["missing"]) == {"Angular", "Vue.js"}
    assert result["additional"] == ["react"]
    assert result["match_percentage"] == 50.0

def test_generate_json_report_valid() -> None:
    candidate_info: dict[str, Any] = {
        "name": "Arjun Sharma",
        "email": "arjun.sharma@email.com",
        "phone": "+91-9876543210",
        "skills": ["Python", "Django", "Docker"],
    }
    match_result = compute_match(
        resume_text="Senior Python Engineer with Django experience.",
        job_text="Python Backend Engineer with Docker and Django.",
        resume_skills=["Python", "Django"],
        job_skills=["Python", "Django", "Docker"],
        use_semantic=False,
    )

    json_report = generate_json_report(
        candidate_info=candidate_info,
        match_result=match_result,
        job_title="Backend Developer",
    )

    assert isinstance(json_report, str)
    parsed = json.loads(json_report)

    assert parsed["job_title"] == "Backend Developer"
    assert parsed["candidate_info"]["name"] == "Arjun Sharma"
    assert "timestamp" in parsed
    assert "match_summary" in parsed
    assert "match_result" in parsed
    assert "improvement_suggestions" in parsed
    assert isinstance(parsed["improvement_suggestions"], list)
    assert len(parsed["improvement_suggestions"]) >= 5

def test_generate_csv_report_valid() -> None:
    candidate_info: dict[str, Any] = {
        "name": "Arjun Sharma",
        "email": "arjun.sharma@email.com",
        "phone": "+91-9876543210",
    }
    match_result = compute_match(
        resume_text="Python engineer with REST APIs and Django.",
        job_text="Python engineer with AWS and Django experience.",
        resume_skills=["Python", "Django"],
        job_skills=["Python", "Django", "AWS"],
        use_semantic=False,
    )

    csv_report = generate_csv_report(
        candidate_info=candidate_info,
        match_result=match_result,
        job_title="Software Developer",
    )

    assert isinstance(csv_report, str)
    assert "Category,Metric / Field,Value" in csv_report
    assert "Software Developer" in csv_report
    assert "Arjun Sharma" in csv_report
    assert "Overall Score" in csv_report
    assert "Matched Skills" in csv_report
    assert "Missing Skills" in csv_report
    assert "Improvement Suggestions" in csv_report

def test_generate_improvement_suggestions() -> None:
    synthetic_match_result: dict[str, Any] = {
        "overall_score": 62.5,
        "tfidf_score": 45.0,
        "semantic_score": 58.0,
        "skill_match_score": 50.0,
        "matched_skills": ["Python", "Git"],
        "missing_skills": ["Docker", "Kubernetes"],
        "additional_skills": ["React"],
    }

    suggestions = generate_improvement_suggestions(synthetic_match_result)

    assert isinstance(suggestions, list)
    assert 5 <= len(suggestions) <= 10
    assert any("Docker" in s for s in suggestions)
    assert any("keyword" in s.lower() for s in suggestions)
    assert any("project" in s.lower() or "narrative" in s.lower() for s in suggestions)
    assert all(isinstance(s, str) and len(s) > 15 for s in suggestions)
