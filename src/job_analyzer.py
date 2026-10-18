from __future__ import annotations

import logging
import re
from typing import Any

from src.skill_extractor import extract_skills, load_skills_database

logger = logging.getLogger(__name__)

REQUIRED_SECTION_PATTERN = re.compile(
    r"^(?:[\s*#\-•]*)(?:requirements|required(?:\s+skills|\s+qualifications|\s+experience)?|"
    r"must\s+have|minimum\s+qualifications|basic\s+qualifications|"
    r"what\s+you(?:'ll|\s+will)?\s+need|what\s+we(?:'re|\s+are)?\s+looking\s+for|"
    r"what\s+you\s+bring|key\s+qualifications|eligibility)[\s:]*$",
    re.IGNORECASE,
)

PREFERRED_SECTION_PATTERN = re.compile(
    r"^(?:[\s*#\-•]*)(?:preferred(?:\s+skills|\s+qualifications|\s+experience)?|"
    r"nice\s+to\s+have|bonus(?:\s+points)?|desired(?:\s+skills|\s+qualifications)?|"
    r"good\s+to\s+have|pluses?|additional\s+qualifications|great\s+to\s+have)[\s:]*$",
    re.IGNORECASE,
)

QUALIFICATIONS_SECTION_PATTERN = re.compile(
    r"^(?:[\s*#\-•]*)(?:education(?:\s+requirements|\s+and\s+experience)?|"
    r"educational\s+background|academic\s+requirements|qualifications)[\s:]*$",
    re.IGNORECASE,
)

OTHER_SECTION_PATTERN = re.compile(
    r"^(?:[\s*#\-•]*)(?:about\s+(?:the\s+role|the\s+company|us)|responsibilities|"
    r"what\s+you(?:'ll|\s+will)?\s+do|duties|job\s+summary|role\s+overview|"
    r"benefits|perks|compensation|salary|how\s+to\s+apply|equal\s+opportunity)[\s:]*$",
    re.IGNORECASE,
)

TITLE_KEYWORDS_PATTERN = re.compile(
    r"\b(?:software\s+engineer|data\s+scientist|machine\s+learning\s+engineer|"
    r"full\s*stack|frontend|front-end|backend|back-end|devops|cloud\s+engineer|"
    r"developer|engineer|architect|manager|lead|analyst|designer|consultant|"
    r"specialist|administrator|programmer|director|intern|associate|officer|"
    r"technician|coordinator|scientist)\b",
    re.IGNORECASE,
)

EXPLICIT_TITLE_PATTERN = re.compile(
    r"^(?:job\s+title|title|position|role)[\s:]+(.+)$",
    re.IGNORECASE,
)

EDUCATION_DEGREE_PATTERN = re.compile(
    r"\b(?:bachelor(?:'s)?|master(?:'s)?|ph\.?d\.?|doctorate|b\.?s\.?|m\.?s\.?|"
    r"b\.?e\.?|m\.?e\.?|b\.?tech|m\.?tech|b\.?c\.?a\.?|m\.?c\.?a\.?|"
    r"associate(?:\s+degree)?|degree\s+in|diploma|computer\s+science|engineering)\b",
    re.IGNORECASE,
)

EXPERIENCE_PATTERNS = [
    re.compile(
        r"\b(?:at\s+least|minimum(?:\s+of)?)\s+\d+(?:\.\d+)?\s*\+?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:-|to)\s*\d+(?:\.\d+)?\s*\+?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+(?:\.\d+)?\s*\+\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:years?|yrs?)\s+(?:of\s+)?experience\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:years?|yrs?)\b",
        re.IGNORECASE,
    ),
]

def extract_skills_from_jd(
    text: str,
    skills_db: dict[str, list[str]] | None = None
) -> dict[str, list[str]]:
    if skills_db is None:
        skills_db = load_skills_database()
    return extract_skills(text, skills_db=skills_db)

def extract_experience_years(text: str) -> str:
    if not text or not isinstance(text, str) or not text.strip():
        return "Not specified"

    for pattern in EXPERIENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            cleaned_match = " ".join(match.group(0).split())
            return cleaned_match

    return "Not specified"

def _clean_bullet(line: str) -> str:
    line = re.sub(r"^[\s*#\-•–—]+", "", line)
    line = re.sub(r"^\d+[\.\)]\s*", "", line)
    return " ".join(line.split())

def _extract_title(lines: list[str]) -> str:
    if not lines:
        return "Not identified"

    for line in lines[:10]:
        explicit_match = EXPLICIT_TITLE_PATTERN.match(line)
        if explicit_match:
            candidate = _clean_bullet(explicit_match.group(1))
            if candidate:
                return candidate

    for line in lines[:8]:
        cleaned = _clean_bullet(line)
        if 4 <= len(cleaned) <= 100 and TITLE_KEYWORDS_PATTERN.search(cleaned):
            if not REQUIRED_SECTION_PATTERN.match(line) and not OTHER_SECTION_PATTERN.match(line):
                return cleaned

    first_cleaned = _clean_bullet(lines[0])
    if 4 <= len(first_cleaned) <= 80 and not first_cleaned.endswith((".", ":", ";")):
        return first_cleaned

    return "Not identified"

def analyze_job_description(
    text: str,
    skills_db: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "title": "Not identified",
            "required_skills": [],
            "preferred_skills": [],
            "qualifications": [],
            "experience_required": "Not specified",
            "raw_text": text or "",
        }

    if skills_db is None:
        skills_db = load_skills_database()
    raw_lines = text.splitlines()
    non_empty_lines = [line.strip() for line in raw_lines if line.strip()]

    current_section = "header"
    sections: dict[str, list[str]] = {
        "header": [],
        "required": [],
        "preferred": [],
        "qualifications": [],
        "other": [],
    }

    for line in non_empty_lines:
        if REQUIRED_SECTION_PATTERN.match(line):
            current_section = "required"
            continue
        elif PREFERRED_SECTION_PATTERN.match(line):
            current_section = "preferred"
            continue
        elif QUALIFICATIONS_SECTION_PATTERN.match(line):
            current_section = "qualifications"
            continue
        elif OTHER_SECTION_PATTERN.match(line):
            current_section = "other"
            continue

        sections[current_section].append(line)

    title = _extract_title(non_empty_lines)

    if sections["required"]:
        req_text = "\n".join(sections["required"])
        extracted_req = extract_skills(req_text, skills_db=skills_db)
        combined_req = extracted_req["technical_skills"] + extracted_req["soft_skills"]
        seen_req: set[str] = set()
        required_skills: list[str] = []
        for s in combined_req:
            if s.lower() not in seen_req:
                seen_req.add(s.lower())
                required_skills.append(s)
    else:
        extracted_all = extract_skills(text, skills_db=skills_db)
        combined_all = extracted_all["technical_skills"] + extracted_all["soft_skills"]
        seen_all: set[str] = set()
        required_skills = []
        for s in combined_all:
            if s.lower() not in seen_all:
                seen_all.add(s.lower())
                required_skills.append(s)

    preferred_skills: list[str] = []
    if sections["preferred"]:
        pref_text = "\n".join(sections["preferred"])
        extracted_pref = extract_skills(pref_text, skills_db=skills_db)
        combined_pref = extracted_pref["technical_skills"] + extracted_pref["soft_skills"]
        req_lower = {s.lower() for s in required_skills}
        seen_pref: set[str] = set()
        for s in combined_pref:
            if s.lower() not in req_lower and s.lower() not in seen_pref:
                seen_pref.add(s.lower())
                preferred_skills.append(s)

    qualifications: list[str] = []
    seen_quals: set[str] = set()

    for line in sections["qualifications"]:
        cleaned = _clean_bullet(line)
        if cleaned and cleaned.lower() not in seen_quals:
            seen_quals.add(cleaned.lower())
            qualifications.append(cleaned)

    for line in non_empty_lines:
        cleaned = _clean_bullet(line)
        if EDUCATION_DEGREE_PATTERN.search(cleaned):
            if cleaned.lower() not in seen_quals:
                seen_quals.add(cleaned.lower())
                qualifications.append(cleaned)

    experience_required = extract_experience_years(text)

    return {
        "title": title,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "qualifications": qualifications,
        "experience_required": experience_required,
        "raw_text": text,
    }
