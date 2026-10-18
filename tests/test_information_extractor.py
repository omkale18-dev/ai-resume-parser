from __future__ import annotations

import pytest

from src.information_extractor import (
    extract_all,
    extract_certifications,
    extract_education,
    extract_email,
    extract_experience,
    extract_name,
    extract_phone,
    extract_projects,
)

SAMPLE_RESUME_TEXT = """Arjun Sharma
arjun.sharma@email.com
+91-9876543210

Education
B.Tech in Computer Science
Indian Institute of Technology Delhi
2016 - 2020

Work Experience
Software Developer, Infosys
June 2020 - December 2022
- Developed REST APIs using Python and Django

Skills
Python, Java, Django, React, Docker, Git

Certifications
AWS Certified Cloud Practitioner
Google Data Analytics Certificate

Projects
E-Commerce Platform - Built with Django and React
Chat Application - Real-time messaging using WebSocket
"""

def test_extract_email_found() -> None:
    text = "Please reach out to candidate at alex.smith@example.org regarding this role."
    email = extract_email(text)

    assert email == "alex.smith@example.org"

def test_extract_email_not_found() -> None:
    text = "Candidate profile with no digital contact method provided."
    email = extract_email(text)

    assert email == "Not found"

def test_extract_email_multiple() -> None:
    text = "Primary contact: primary.dev@domain.com, Alternative: backup.dev@domain.com"
    email = extract_email(text)

    assert email == "primary.dev@domain.com"

def test_extract_phone_found_indian() -> None:
    text_prefixed = "Candidate contact phone: +91-9876543210"
    phone_prefixed = extract_phone(text_prefixed)
    assert "9876543210" in phone_prefixed

    text_plain = "Phone: 9876543210"
    phone_plain = extract_phone(text_plain)
    assert phone_plain == "9876543210"

def test_extract_phone_found_us() -> None:
    text_standard = "Contact me at 555-123-4567 or via mail."
    phone_standard = extract_phone(text_standard)
    assert phone_standard == "555-123-4567"

    text_parentheses = "Office: (555) 234-5678."
    phone_parentheses = extract_phone(text_parentheses)
    assert "(555) 234-5678" in phone_parentheses

def test_extract_phone_not_found() -> None:
    text = "There is no contact phone number listed on this resume."
    phone = extract_phone(text)

    assert phone == "Not found"

def test_extract_name_found() -> None:
    name = extract_name(SAMPLE_RESUME_TEXT)
    assert name == "Arjun Sharma"

    custom_text = "Priya Sundaram\npriya@example.com\nBangalore, India"
    assert extract_name(custom_text) == "Priya Sundaram"

def test_extract_name_not_found() -> None:
    text_unnamed = (
        "RESUME\n"
        "Curriculum Vitae\n"
        "contact@company.com\n"
        "Software Engineer\n"
        "+1-555-019-2834\n"
    )
    name = extract_name(text_unnamed)
    assert name == "Not found"

    assert extract_name("") == "Not found"

def test_extract_education_found() -> None:
    education_entries = extract_education(SAMPLE_RESUME_TEXT)

    assert isinstance(education_entries, list)
    assert len(education_entries) >= 1

    entry = education_entries[0]
    assert "degree" in entry
    assert "institution" in entry
    assert "year" in entry

    assert "B.Tech" in entry["degree"]
    assert "Indian Institute of Technology" in entry["institution"]
    assert "2016 - 2020" in entry["year"]

def test_extract_education_not_found() -> None:
    text_no_edu = "Candidate possesses 10 years of self-taught engineering expertise."
    education_entries = extract_education(text_no_edu)

    assert education_entries == []
    assert extract_education("") == []

def test_extract_experience_found() -> None:
    experience_entries = extract_experience(SAMPLE_RESUME_TEXT)

    assert isinstance(experience_entries, list)
    assert len(experience_entries) >= 1

    entry = experience_entries[0]
    assert "title" in entry
    assert "company" in entry
    assert "duration" in entry

    assert "Software Developer" in entry["title"]
    assert "Infosys" in entry["company"]
    assert "2020" in entry["duration"]

def test_extract_experience_not_found() -> None:
    text_no_exp = "Fresh graduate seeking entry-level opportunities."
    experience_entries = extract_experience(text_no_exp)

    assert experience_entries == []
    assert extract_experience("") == []

def test_extract_certifications_found() -> None:
    certifications = extract_certifications(SAMPLE_RESUME_TEXT)

    assert isinstance(certifications, list)
    assert len(certifications) >= 2
    assert any("AWS Certified Cloud Practitioner" in c for c in certifications)
    assert any("Google Data Analytics Certificate" in c for c in certifications)

def test_extract_certifications_not_found() -> None:
    text_no_cert = "Summary\nSoftware engineer with strong background in systems design."
    certifications = extract_certifications(text_no_cert)

    assert certifications == []
    assert extract_certifications("") == []

def test_extract_projects_found() -> None:
    projects = extract_projects(SAMPLE_RESUME_TEXT)

    assert isinstance(projects, list)
    assert len(projects) >= 2
    assert any("E-Commerce Platform" in p for p in projects)
    assert any("Chat Application" in p for p in projects)

def test_extract_projects_not_found() -> None:
    text_no_proj = "Summary\nFocused entirely on enterprise consulting."
    projects = extract_projects(text_no_proj)

    assert projects == []
    assert extract_projects("") == []

def test_extract_all_complete() -> None:
    all_data = extract_all(SAMPLE_RESUME_TEXT)

    assert isinstance(all_data, dict)
    expected_keys = {
        "name",
        "email",
        "phone",
        "education",
        "experience",
        "certifications",
        "projects",
    }
    assert expected_keys.issubset(all_data.keys())

    assert all_data["name"] == "Arjun Sharma"
    assert all_data["email"] == "arjun.sharma@email.com"
    assert "9876543210" in all_data["phone"]
    assert len(all_data["education"]) >= 1
    assert len(all_data["experience"]) >= 1
    assert len(all_data["certifications"]) >= 1
    assert len(all_data["projects"]) >= 1

def test_extract_all_empty_text() -> None:
    empty_data = extract_all("")

    assert empty_data["name"] == "Not found"
    assert empty_data["email"] == "Not found"
    assert empty_data["phone"] == "Not found"
    assert empty_data["education"] == []
    assert empty_data["experience"] == []
    assert empty_data["certifications"] == []
    assert empty_data["projects"] == []
