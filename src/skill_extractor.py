from __future__ import annotations

import functools
import json
import logging
import re
from pathlib import Path
from typing import Any

try:
    from src.text_preprocessor import normalize_skill_name
except ImportError:
    def normalize_skill_name(skill: str) -> str:
        if not skill:
            return ""
        return " ".join(skill.strip().lower().split())

logger = logging.getLogger(__name__)

DEFAULT_TECHNICAL_SKILLS: list[str] = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "SQL", "HTML", "CSS",
    "React", "Angular", "Vue.js", "Django", "Flask", "FastAPI", "Spring Boot",
    "Node.js", "Express.js", "Next.js", ".NET", "ASP.NET", "PostgreSQL",
    "MySQL", "MongoDB", "Redis", "SQLite", "Oracle", "AWS", "Azure", "GCP",
    "Docker", "Kubernetes", "Terraform", "CI/CD", "Git", "GitHub", "Linux",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn",
    "Pandas", "NumPy", "NLP", "REST API", "Microservices", "Agile", "Scrum"
]

DEFAULT_SOFT_SKILLS: list[str] = [
    "Leadership", "Communication", "Teamwork", "Problem Solving",
    "Critical Thinking", "Time Management", "Adaptability", "Creativity",
    "Collaboration", "Project Management", "Public Speaking", "Negotiation",
    "Conflict Resolution", "Decision Making", "Mentoring", "Self-Motivation",
    "Attention to Detail", "Organization", "Work Ethic", "Flexibility",
    "Analytical Thinking", "Interpersonal Skills", "Active Listening", "Empathy"
]

def load_skills_database(filepath: str = "data/skills.json") -> dict[str, list[str]]:
    path = Path(filepath)

    if not path.is_file():
        project_root = Path(__file__).resolve().parent.parent
        alt_path = project_root / filepath
        if alt_path.is_file():
            path = alt_path

    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)

            tech_skills = data.get("technical_skills")
            soft_skills = data.get("soft_skills")

            if isinstance(tech_skills, list) and isinstance(soft_skills, list):
                return {
                    "technical_skills": [str(s).strip() for s in tech_skills if str(s).strip()],
                    "soft_skills": [str(s).strip() for s in soft_skills if str(s).strip()],
                }
            logger.warning(
                "Invalid structure in %s; expected 'technical_skills' and "
                "'soft_skills' lists. Using default minimal skill set.",
                filepath
            )
        except Exception as exc:
            logger.warning(
                "Failed to parse skills database from %s: %s. Using default minimal skill set.",
                filepath,
                exc
            )
    else:
        logger.warning(
            "Skills database file not found at %s. Using default minimal skill set.",
            filepath
        )

    return {
        "technical_skills": list(DEFAULT_TECHNICAL_SKILLS),
        "soft_skills": list(DEFAULT_SOFT_SKILLS),
    }

@functools.lru_cache(maxsize=2048)
def _compile_skill_pattern(skill: str) -> re.Pattern[str]:
    cleaned = skill.strip()
    words = cleaned.split()
    escaped_tokens = [re.escape(word) for word in words]
    core_pattern = r"\s+".join(escaped_tokens)

    if cleaned and cleaned[0].isalnum():
        prefix = r"(?<![\w\-])"
    else:
        prefix = r"(?<!\S)"

    suffix = r"(?![\w+#])"

    return re.compile(rf"{prefix}{core_pattern}{suffix}", re.IGNORECASE)

def extract_skills(
    text: str,
    skills_db: dict[str, list[str]] | None = None
) -> dict[str, list[str]]:
    if not text or not isinstance(text, str) or not text.strip():
        return {"technical_skills": [], "soft_skills": []}

    if skills_db is None:
        skills_db = load_skills_database()

    tech_catalog = skills_db.get("technical_skills", [])
    soft_catalog = skills_db.get("soft_skills", [])

    extracted_tech: list[str] = []
    extracted_soft: list[str] = []

    for skill in tech_catalog:
        if not skill or not skill.strip():
            continue
        pattern = _compile_skill_pattern(skill)
        if pattern.search(text):
            extracted_tech.append(skill)

    for skill in soft_catalog:
        if not skill or not skill.strip():
            continue
        pattern = _compile_skill_pattern(skill)
        if pattern.search(text):
            extracted_soft.append(skill)

    return {
        "technical_skills": extracted_tech,
        "soft_skills": extracted_soft,
    }

def match_skills_to_requirements(
    candidate_skills: list[str],
    required_skills: list[str]
) -> dict[str, Any]:
    cand_norm_map: dict[str, str] = {}
    for skill in candidate_skills:
        if not skill or not isinstance(skill, str):
            continue
        norm = normalize_skill_name(skill)
        if norm and norm not in cand_norm_map:
            cand_norm_map[norm] = skill.strip()

    req_norm_map: dict[str, str] = {}
    for skill in required_skills:
        if not skill or not isinstance(skill, str):
            continue
        norm = normalize_skill_name(skill)
        if norm and norm not in req_norm_map:
            req_norm_map[norm] = skill.strip()

    matched: list[str] = []
    missing: list[str] = []

    for norm, original_req in req_norm_map.items():
        if norm in cand_norm_map:
            matched.append(original_req)
        else:
            missing.append(original_req)

    additional: list[str] = []
    for norm, original_cand in cand_norm_map.items():
        if norm not in req_norm_map:
            additional.append(original_cand)

    if req_norm_map:
        raw_percentage = (len(matched) / len(req_norm_map)) * 100.0
        match_percentage = round(min(100.0, max(0.0, raw_percentage)), 2)
    else:
        match_percentage = 100.0

    return {
        "matched": matched,
        "missing": missing,
        "additional": additional,
        "match_percentage": match_percentage,
    }
