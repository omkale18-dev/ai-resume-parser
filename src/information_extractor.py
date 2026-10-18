import re
from typing import Any

from src.text_preprocessor import normalize_text

SECTION_PATTERNS: dict[str, list[str]] = {
    "education": [
        "education",
        "academic background",
        "academics",
        "educational qualification",
        "educational qualifications",
        "academic qualifications",
        "academic history",
        "education and credentials",
        "education & credentials",
        "degrees",
        "qualifications",
    ],
    "experience": [
        "work experience",
        "professional experience",
        "experience",
        "employment history",
        "work history",
        "employment",
        "relevant experience",
        "career history",
        "internships",
        "professional background",
        "working experience",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "licenses & certifications",
        "certifications & licenses",
        "professional certifications",
        "courses & certifications",
        "licenses and certifications",
        "accreditations",
        "certifications and courses",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
        "selected projects",
        "technical projects",
        "side projects",
        "notable projects",
        "project work",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "key skills",
        "skills & abilities",
        "tools & technologies",
        "areas of expertise",
    ],
    "summary": [
        "summary",
        "professional summary",
        "career objective",
        "objective",
        "profile",
        "about me",
        "personal profile",
        "executive summary",
        "overview",
    ],
}

_EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

_PHONE_REGEXES: list[re.Pattern[str]] = [
    re.compile(r"(?:\+|00)[1-9]\d{0,3}[-.\s]?(?:\(?\d{1,5}\)?[-.\s]?){1,4}\d{2,5}"),
    re.compile(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
    re.compile(r"(?:(?:\+?91|0)[-.\s]?)?[6-9]\d{4}[-.\s]?\d{5}\b"),
    re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),
    re.compile(r"\b[6-9]\d{9}\b"),
]

_DISALLOWED_NAME_TOKENS: frozenset[str] = frozenset(
    {
        "resume",
        "curriculum",
        "vitae",
        "cv",
        "profile",
        "summary",
        "objective",
        "contact",
        "education",
        "experience",
        "skills",
        "projects",
        "certifications",
        "work",
        "personal",
        "details",
        "portfolio",
        "address",
        "phone",
        "email",
        "page",
        "linkedin",
        "github",
        "website",
    }
)

_JOB_TITLE_TOKENS: frozenset[str] = frozenset(
    {
        "senior",
        "junior",
        "lead",
        "staff",
        "principal",
        "chief",
        "software",
        "engineer",
        "developer",
        "architect",
        "data",
        "scientist",
        "analyst",
        "product",
        "project",
        "manager",
        "designer",
        "consultant",
        "intern",
        "administrator",
        "specialist",
        "executive",
        "director",
        "officer",
        "full",
        "stack",
        "frontend",
        "backend",
        "devops",
        "cloud",
        "qa",
        "test",
        "security",
    }
)

_DEGREE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(Bachelor\s+of\s+[A-Za-z\s&]+|Master\s+of\s+[A-Za-z\s&]+|Doctor\s+of\s+[A-Za-z\s&]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Bachelor'?s?(?:\s+Degree)?(?:\s+(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"Master'?s?(?:\s+Degree)?(?:\s+(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"Doctorate(?:\s+(?:in|of)\s+[A-Za-z\s&]+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(B\.?\s*Tech(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*E(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*Sc(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*S(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*C\.?\s*A(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*B\.?\s*A(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*Com(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"B\.?\s*A(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(M\.?\s*Tech(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*E(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*Sc(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*S(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*C\.?\s*A(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*B\.?\s*A(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*Com(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"M\.?\s*A(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Ph\.?\s*D(?:\.|\b)(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Diploma(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?|"
        r"Associate(?:\s+Degree)?(?:\s*(?:in|of)\s+[A-Za-z\s&]+)?)",
        re.IGNORECASE,
    ),
]

_INSTITUTION_KEYWORDS: list[str] = [
    "university",
    "college",
    "institute",
    "school",
    "academy",
    "polytechnic",
    "campus",
    "iit",
    "nit",
    "bits",
    "mit",
    "stanford",
    "harvard",
    "berkeley",
    "oxford",
    "cambridge",
]

_JOB_TITLE_PATTERNS: list[str] = [
    r"\b(?:Senior|Junior|Lead|Principal|Staff|Chief|Head|Associate|Assistant)?\s*"
    r"(?:Software|Systems?|Full\s*Stack|Frontend|Front-end|Backend|Back-end|Web|Mobile|iOS|Android|"
    r"DevOps|Cloud|Data|Machine\s*Learning|ML|AI|Deep\s*Learning|NLP|Platform|Site\s*Reliability|SRE|"
    r"QA|Quality\s*Assurance|Test|Automation|Security|Cybersecurity|Network|Database|BI|Business\s*Intelligence)\s+"
    r"(?:Engineer|Developer|Architect|Scientist|Analyst|Programmer|Specialist)\b",
    r"\b(?:Senior|Junior|Lead|Associate)?\s*"
    r"(?:Product|Project|Program|Engineering|Technical|Operations|IT|General)\s+"
    r"(?:Manager|Director|Lead|Coordinator|Owner)\b",
    r"\b(?:Business|Data|Financial|Systems?|Research|Operations|Security)\s+Analyst\b",
    r"\b(?:UI|UX|UI/UX|Product|Graphic|Web)\s+Designer\b",
    r"\b(?:Software\s+Engineering\s+Intern|Software\s+Intern|Data\s+Science\s+Intern|Research\s+Intern|Intern)\b",
    r"\b(?:Solutions\s+Architect|Enterprise\s+Architect|Cloud\s+Architect|Technical\s+Architect)\b",
    r"\b(?:Technical\s+Consultant|Senior\s+Consultant|Consultant|Associate\s+Consultant)\b",
    r"\b(?:System\s+Administrator|Database\s+Administrator|Network\s+Administrator)\b",
    r"\b(?:Founder|Co-Founder|CTO|CEO|COO|VP\s+of\s+Engineering)\b",
]

_COMPANY_INDICATORS: list[str] = [
    r"\bInc\.?",
    r"\bLtd\.?",
    r"\bLLC\b",
    r"\bCorp\.?",
    r"\bCorporation\b",
    r"\bTechnologies\b",
    r"\bSolutions\b",
    r"\bSystems\b",
    r"\bLabs\b",
    r"\bSoftware\b",
    r"\bServices\b",
    r"\bPvt\.?\s*Ltd\.?",
    r"\bPte\.?\s*Ltd\.?",
    r"\bEnterprises\b",
    r"\bGoogle\b",
    r"\bMicrosoft\b",
    r"\bAmazon\b",
    r"\bApple\b",
    r"\bMeta\b",
    r"\bNetflix\b",
    r"\bUber\b",
    r"\bIBM\b",
    r"\bOracle\b",
    r"\bIntel\b",
    r"\bCisco\b",
    r"\bTCS\b",
    r"\bInfosys\b",
    r"\bWipro\b",
    r"\bAccenture\b",
    r"\bCognizant\b",
    r"\bCapgemini\b",
]

_DATE_RANGE_REGEX = re.compile(
    r"\b(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|"
    r"\d{1,2}/\d{4}|\d{4})\s*[-–—to]+\s*"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|"
    r"\d{1,2}/\d{4}|\d{4}|[Pp]resent|[Cc]urrent))\b",
    re.IGNORECASE,
)

_YEAR_RANGE_REGEX = re.compile(
    r"\b(199\d|20[0-2]\d|2030)\s*[-–—to]+\s*(199\d|20[0-2]\d|2030)\b"
)
_SINGLE_YEAR_REGEX = re.compile(r"\b(199\d|20[0-2]\d|2030)\b")

def _is_section_header(line: str) -> tuple[bool, str | None]:
    clean_line = re.sub(r"^[\s#*•\-–—_~:]+|[\s:*•\-–—_~]+$", "", line).strip()
    if not clean_line or len(clean_line) > 50:
        return False, None

    if len(clean_line.split()) > 4:
        return False, None

    lower_line = clean_line.lower()
    for category, keywords in SECTION_PATTERNS.items():
        if lower_line in keywords:
            return True, category
        for kw in keywords:
            if lower_line == kw or lower_line.startswith(kw + " "):
                return True, category

    return False, None

def _get_section_text(text: str, target_section: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    lines = text.splitlines()
    target_lines: list[str] = []
    in_target = False

    for line in lines:
        is_header, header_cat = _is_section_header(line)
        if is_header:
            if header_cat == target_section:
                in_target = True
                continue
            elif in_target:
                break
        elif in_target:
            target_lines.append(line)

    return "\n".join(target_lines).strip()

def extract_email(text: str) -> str:
    if not text or not isinstance(text, str):
        return "Not found"

    match = _EMAIL_REGEX.search(text)
    if match:
        email = match.group(0).strip().rstrip(".,;:)")
        return email

    return "Not found"

def extract_phone(text: str) -> str:
    if not text or not isinstance(text, str):
        return "Not found"

    for pattern in _PHONE_REGEXES:
        for match in pattern.finditer(text):
            candidate = match.group(0).strip().rstrip(".,;:")
            digits = re.sub(r"\D", "", candidate)
            if 10 <= len(digits) <= 15:
                return candidate

    return "Not found"

def extract_name(text: str) -> str:
    if not text or not isinstance(text, str):
        return "Not found"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:30]:
        if "@" in line or any(
            url_marker in line.lower()
            for url_marker in ["http", "www.", ".com", "github", "linkedin"]
        ):
            continue

        if re.search(r"\d{3,}", line):
            continue

        if re.search(r"[<>{}|=/_*#~+;!?]", line):
            continue

        is_header, _ = _is_section_header(line)
        if is_header:
            continue

        words = [w.strip(".,") for w in line.split() if w.strip(".,")]
        if not (2 <= len(words) <= 4):
            continue

        lower_words = [w.lower() for w in words]
        if any(w in _DISALLOWED_NAME_TOKENS for w in lower_words):
            continue

        if all(w in _JOB_TITLE_TOKENS for w in lower_words):
            continue

        is_valid_name = True
        for word in words:
            if not re.match(r"^[A-Z][A-Za-z.\'-]*$", word):
                is_valid_name = False
                break

        if is_valid_name:
            cleaned_name = " ".join(words)
            return cleaned_name

    return "Not found"

def extract_education(text: str) -> list[dict[str, str]]:
    if not text or not isinstance(text, str):
        return []

    edu_text = _get_section_text(text, "education")
    search_text = edu_text if edu_text else text

    raw_lines = [line.strip() for line in search_text.splitlines() if line.strip()]
    if not raw_lines:
        return []

    entries: list[dict[str, str]] = []
    seen_entries: set[tuple[str, str]] = set()

    for idx, line in enumerate(raw_lines):
        degree_match = None
        matched_pattern = None

        for pattern in _DEGREE_PATTERNS:
            match = pattern.search(line)
            if match:
                degree_match = match
                matched_pattern = pattern
                break

        if not degree_match:
            continue

        raw_degree = degree_match.group(0).strip().rstrip(".,;:-|")
        raw_degree = re.sub(
            r"\s*[-–—|]\s*$", "", raw_degree, flags=re.IGNORECASE
        )

        institution = "Not found"
        candidate_lines = []
        if idx > 0:
            candidate_lines.append(raw_lines[idx - 1])
        candidate_lines.append(line)
        if idx + 1 < len(raw_lines):
            candidate_lines.append(raw_lines[idx + 1])
        if idx + 2 < len(raw_lines):
            candidate_lines.append(raw_lines[idx + 2])

        for cand in candidate_lines:
            cand_lower = cand.lower()
            if any(
                re.search(r"\b" + re.escape(ik) + r"\b", cand_lower)
                for ik in _INSTITUTION_KEYWORDS
            ):
                cand_clean = cand
                if cand == line and matched_pattern:
                    cand_clean = matched_pattern.sub("", cand_clean)
                cand_clean = _SINGLE_YEAR_REGEX.sub("", cand_clean)
                cand_clean = re.sub(
                    r"^[\s,.\-–—|]+|[\s,.\-–—|]+$", "", cand_clean
                ).strip()
                if cand_clean and len(cand_clean) >= 3:
                    institution = cand_clean
                    break

        if institution == "Not found":
            for offset in [1, -1]:
                target_idx = idx + offset
                if 0 <= target_idx < len(raw_lines):
                    adj_line = raw_lines[target_idx]
                    adj_clean = _SINGLE_YEAR_REGEX.sub("", adj_line).strip(" ,.-|")
                    if (
                        adj_clean
                        and 2 <= len(adj_clean.split()) <= 8
                        and not any(p.search(adj_clean) for p in _DEGREE_PATTERNS)
                    ):
                        institution = adj_clean
                        break

        year = "Not found"
        for cand in [line] + candidate_lines:
            year_range_match = _YEAR_RANGE_REGEX.search(cand)
            if year_range_match:
                year = year_range_match.group(0).strip()
                break
            year_single_match = _SINGLE_YEAR_REGEX.search(cand)
            if year_single_match:
                year = year_single_match.group(0).strip()
                break

        key = (raw_degree.lower(), year)
        if key not in seen_entries:
            seen_entries.add(key)
            entries.append(
                {
                    "degree": raw_degree,
                    "institution": institution,
                    "year": year,
                }
            )

    return entries

def extract_experience(text: str) -> list[dict[str, str]]:
    if not text or not isinstance(text, str):
        return []

    exp_text = _get_section_text(text, "experience")
    search_text = exp_text if exp_text else text

    raw_lines = [line.strip() for line in search_text.splitlines() if line.strip()]
    if not raw_lines:
        return []

    entries: list[dict[str, str]] = []
    seen_titles: set[str] = set()

    combined_job_regex = re.compile(
        "|".join(f"(?:{p})" for p in _JOB_TITLE_PATTERNS),
        re.IGNORECASE,
    )

    for idx, line in enumerate(raw_lines):
        match = combined_job_regex.search(line)
        if not match:
            continue

        raw_title = match.group(0).strip().rstrip(".,;:-|")
        title_lower = raw_title.lower()

        company = "Not found"
        at_match = re.search(r"\bat\s+([A-Z][A-Za-z0-9\s&.,'-]+)", line)
        if at_match:
            comp_candidate = at_match.group(1).strip().rstrip(".,;:-|")
            comp_candidate = _DATE_RANGE_REGEX.sub("", comp_candidate).strip()
            if comp_candidate:
                company = comp_candidate

        if company == "Not found":
            segments = [
                s.strip() for s in re.split(r"[-–—|,]\s*", line) if s.strip()
            ]
            for seg in segments:
                if seg.lower() != title_lower and not _DATE_RANGE_REGEX.search(seg):
                    if any(
                        re.search(ind, seg, re.IGNORECASE) for ind in _COMPANY_INDICATORS
                    ) or (len(seg.split()) <= 4 and seg[0].isupper()):
                        company = seg
                        break

        if company == "Not found":
            for offset in [-1, 1]:
                target_idx = idx + offset
                if 0 <= target_idx < len(raw_lines):
                    cand_line = raw_lines[target_idx]
                    if not combined_job_regex.search(
                        cand_line
                    ) and not _DATE_RANGE_REGEX.search(cand_line):
                        if any(
                            re.search(ind, cand_line, re.IGNORECASE)
                            for ind in _COMPANY_INDICATORS
                        ):
                            company = cand_line.strip().rstrip(".,;:-|")
                            break
                        elif (
                            1 <= len(cand_line.split()) <= 5
                            and cand_line[0].isupper()
                            and not _is_section_header(cand_line)[0]
                        ):
                            company = cand_line.strip().rstrip(".,;:-|")
                            break

        duration = "Not found"
        cand_lines = [line]
        if idx > 0:
            cand_lines.append(raw_lines[idx - 1])
        if idx + 1 < len(raw_lines):
            cand_lines.append(raw_lines[idx + 1])
        if idx + 2 < len(raw_lines):
            cand_lines.append(raw_lines[idx + 2])

        for cand in cand_lines:
            date_match = _DATE_RANGE_REGEX.search(cand)
            if date_match:
                duration = date_match.group(0).strip()
                break

        key = f"{title_lower}_{company.lower()}"
        if key not in seen_titles:
            seen_titles.add(key)
            entries.append(
                {
                    "title": raw_title,
                    "company": company,
                    "duration": duration,
                }
            )

    return entries

def extract_certifications(text: str) -> list[str]:
    if not text or not isinstance(text, str):
        return []

    cert_text = _get_section_text(text, "certifications")
    items: list[str] = []
    seen: set[str] = set()

    if cert_text:
        for line in cert_text.splitlines():
            clean = re.sub(r"^[\s*•▪\-–—\d.)]+", "", line).strip()
            if clean and len(clean) >= 3 and not _is_section_header(clean)[0]:
                clean_norm = normalize_text(clean)
                if clean_norm.lower() not in seen:
                    seen.add(clean_norm.lower())
                    items.append(clean)
    else:
        prominent_certs = [
            r"AWS\s+Certified(?:\s+[A-Za-z0-9\s\-–—]+)?",
            r"Google\s+Cloud\s+Certified(?:\s+[A-Za-z0-9\s\-–—]+)?",
            r"Microsoft\s+Certified(?:\s+[A-Za-z0-9\s\-–—]+)?",
            r"Azure\s+Certified(?:\s+[A-Za-z0-9\s\-–—]+)?",
            r"Certified\s+Kubernetes\s+(?:Administrator|Application\s+Developer)\b",
            r"\bCKA\b|\bCKAD\b",
            r"\bPMP\b|\bProject\s+Management\s+Professional\b",
            r"\bCISSP\b",
            r"\bCompTIA\s+[A-Za-z0-9+]+\b",
            r"Certified\s+Scrum\s*Master\b|\bCSM\b",
        ]
        combined_certs = re.compile("|".join(prominent_certs), re.IGNORECASE)
        for match in combined_certs.finditer(text):
            found_cert = match.group(0).strip().rstrip(".,;:-|")
            if found_cert.lower() not in seen:
                seen.add(found_cert.lower())
                items.append(found_cert)

    return items

def extract_projects(text: str) -> list[str]:
    if not text or not isinstance(text, str):
        return []

    proj_text = _get_section_text(text, "projects")
    if not proj_text:
        return []

    raw_lines = [line.strip() for line in proj_text.splitlines() if line.strip()]
    if not raw_lines:
        return []

    items: list[str] = []
    seen: set[str] = set()

    for line in raw_lines:
        if _is_section_header(line)[0]:
            break

        cleaned = re.sub(r"^[\s*•▪\-–—\d.)]+", "", line).strip()
        if not cleaned or len(cleaned) < 3:
            continue

        normalized = normalize_text(cleaned)
        if normalized.lower() not in seen:
            seen.add(normalized.lower())
            items.append(cleaned)

    return items

def extract_all(text: str) -> dict[str, Any]:
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "certifications": extract_certifications(text),
        "projects": extract_projects(text),
    }
