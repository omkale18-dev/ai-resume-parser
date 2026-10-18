from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

def generate_match_summary(match_result: dict[str, Any]) -> str:
    overall_score = float(match_result.get("overall_score", 0.0))
    skill_score = float(match_result.get("skill_match_score", 0.0))
    matched_skills = match_result.get("matched_skills", [])
    missing_skills = match_result.get("missing_skills", [])
    semantic_score = match_result.get("semantic_score")

    if overall_score >= 85.0:
        tier_desc = "exceptional alignment"
        recommendation = "The candidate is strongly recommended for immediate technical interview consideration."
    elif overall_score >= 70.0:
        tier_desc = "strong alignment"
        recommendation = "The candidate presents a solid profile that warrants advancement to an initial interview round."
    elif overall_score >= 50.0:
        tier_desc = "moderate alignment"
        recommendation = "The candidate meets several core criteria but may require skill bridging or targeted evaluation."
    else:
        tier_desc = "limited alignment"
        recommendation = "Significant skill and background gaps exist relative to the core requirements of this role."

    sentence_1 = (
        f"The candidate demonstrates {tier_desc} with the target role, "
        f"achieving an overall match score of {overall_score:.1f}%."
    )

    total_skills = len(matched_skills) + len(missing_skills)
    sem_text = f" and a semantic similarity of {semantic_score:.1f}%" if semantic_score is not None else ""
    if total_skills > 0:
        skills_text = f"satisfies {len(matched_skills)} of {total_skills} required skills ({skill_score:.1f}% skill match){sem_text}"
    else:
        skills_text = f"achieved a skill match score of {skill_score:.1f}%{sem_text}"

    if missing_skills:
        missing_preview = ", ".join(missing_skills[:3])
        if len(missing_skills) > 3:
            missing_preview += f" (+{len(missing_skills) - 3} more)"
        sentence_2 = f"They {skills_text}, with notable gaps in {missing_preview}."
    else:
        sentence_2 = f"They {skills_text}, successfully meeting all explicitly listed skills."

    sentence_3 = recommendation

    return f"{sentence_1} {sentence_2} {sentence_3}"

def generate_improvement_suggestions(match_result: dict[str, Any]) -> list[str]:
    suggestions: list[str] = []

    missing_skills = match_result.get("missing_skills", [])
    tfidf_score = float(match_result.get("tfidf_score", 0.0))
    semantic_score = match_result.get("semantic_score")
    skill_score = float(match_result.get("skill_match_score", 0.0))
    additional_skills = match_result.get("additional_skills", [])

    if missing_skills:
        top_missing = ", ".join(missing_skills[:4])
        suggestions.append(
            f"Prioritize building and showcasing hands-on experience with missing required skills: {top_missing}."
        )
        if len(missing_skills) > 1:
            primary_missing = missing_skills[0]
            suggestions.append(
                f"Develop a portfolio project or public repository demonstrating practical application of {primary_missing}."
            )

    if tfidf_score < 60.0:
        suggestions.append(
            "Incorporate exact keywords, tools, and technical terms directly from the job description into your experience section."
        )
        suggestions.append(
            "Align your section headers and role titles with standard industry nomenclature to improve ATS keyword extraction."
        )
    else:
        suggestions.append(
            "Maintain keyword consistency across all job descriptions while ensuring natural readability for human recruiters."
        )

    if semantic_score is not None and semantic_score < 65.0:
        suggestions.append(
            "Revise project narratives to more explicitly reflect the engineering workflows, design patterns, and scale mentioned in the job description."
        )
        suggestions.append(
            "Emphasize end-to-end responsibility, problem-solving methodologies, and system architectural decisions in your bullet points."
        )

    if skill_score < 75.0:
        suggestions.append(
            "Pursue recognized industry certifications or accredited courses to validate proficiency in the role's essential technologies."
        )

    if additional_skills:
        top_additional = ", ".join(additional_skills[:3])
        suggestions.append(
            f"Highlight your unique complementary competencies ({top_additional}) in your summary to demonstrate added versatility."
        )

    suggestions.append(
        "Quantify your career accomplishments with concrete business metrics (e.g., '% performance improvement', '$ cost reduction', 'user scale')."
    )
    suggestions.append(
        "Craft a targeted professional summary at the very top of your resume tailored specifically to this target position."
    )
    suggestions.append(
        "Format project bullet points using the Action Verb + Context + Measurable Result (STAR/CAR) framework."
    )
    suggestions.append(
        "Ensure your resume format uses standard clean fonts, consistent date styling, and bulleted lists for seamless ATS parsing."
    )

    return suggestions[:10]

def generate_json_report(
    candidate_info: dict[str, Any],
    match_result: dict[str, Any],
    job_title: str = ""
) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    match_summary = generate_match_summary(match_result)
    suggestions = generate_improvement_suggestions(match_result)

    report_payload: dict[str, Any] = {
        "timestamp": timestamp,
        "job_title": job_title.strip() if job_title else "Not specified",
        "candidate_info": candidate_info,
        "match_summary": match_summary,
        "match_result": match_result,
        "improvement_suggestions": suggestions,
    }

    return json.dumps(report_payload, indent=2, default=str)

def generate_csv_report(
    candidate_info: dict[str, Any],
    match_result: dict[str, Any],
    job_title: str = ""
) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    timestamp = datetime.now(timezone.utc).isoformat()
    summary = generate_match_summary(match_result)
    suggestions = generate_improvement_suggestions(match_result)

    writer.writerow(["Category", "Metric / Field", "Value"])

    writer.writerow(["Metadata", "Timestamp", timestamp])
    writer.writerow(["Metadata", "Job Title", job_title.strip() if job_title else "Not specified"])

    for field_name, value in candidate_info.items():
        if isinstance(value, (list, tuple)):
            formatted_val = ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            formatted_val = json.dumps(value, default=str)
        else:
            formatted_val = str(value)
        readable_field = field_name.replace("_", " ").title()
        writer.writerow(["Candidate Info", readable_field, formatted_val])

    overall_score = match_result.get("overall_score", 0.0)
    tfidf_score = match_result.get("tfidf_score", 0.0)
    sem_score = match_result.get("semantic_score")
    skill_score = match_result.get("skill_match_score", 0.0)

    writer.writerow(["Match Scores", "Overall Score", f"{float(overall_score):.2f}%"])
    writer.writerow(["Match Scores", "TF-IDF Score", f"{float(tfidf_score):.2f}%"])
    writer.writerow(
        ["Match Scores", "Semantic Score", f"{float(sem_score):.2f}%" if sem_score is not None else "N/A"]
    )
    writer.writerow(["Match Scores", "Skill Match Score", f"{float(skill_score):.2f}%"])

    matched_skills = match_result.get("matched_skills", [])
    missing_skills = match_result.get("missing_skills", [])
    additional_skills = match_result.get("additional_skills", [])

    writer.writerow(["Skills Analysis", "Matched Skills", "; ".join(str(s) for s in matched_skills)])
    writer.writerow(["Skills Analysis", "Missing Skills", "; ".join(str(s) for s in missing_skills)])
    writer.writerow(["Skills Analysis", "Additional Skills", "; ".join(str(s) for s in additional_skills)])

    writer.writerow(["Summary", "Explanation", match_result.get("explanation", "")])
    writer.writerow(["Summary", "Match Summary", summary])

    for index, suggestion in enumerate(suggestions, start=1):
        writer.writerow(["Improvement Suggestions", f"Suggestion {index}", suggestion])

    return output.getvalue()
