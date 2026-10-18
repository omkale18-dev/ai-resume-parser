from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent

try:
    from src.resume_extractor import extract_text, validate_file
    from src.information_extractor import extract_all
    from src.skill_extractor import extract_skills, load_skills_database, match_skills_to_requirements
    from src.job_analyzer import analyze_job_description
    from src.resume_matcher import (
        compute_match,
        get_sentence_transformer_model,
        semantic_similarity,
        tfidf_similarity,
    )
    from src.report_generator import (
        generate_csv_report,
        generate_improvement_suggestions,
        generate_json_report,
        generate_match_summary,
    )
except ImportError as exc:
    st.error(f"Critical module import failure: {exc}. Please verify project dependencies.")
    raise

@st.cache_resource(show_spinner="Loading semantic SentenceTransformer model...")
def load_cached_semantic_model(model_name: str = "all-MiniLM-L6-v2") -> Any:
    try:
        return get_sentence_transformer_model(model_name)
    except Exception as exc:
        logger.warning("Could not pre-load SentenceTransformer model: %s", exc)
        return None

@st.cache_data(show_spinner=False)
def get_cached_skills_db(filepath: str = "data/skills.json") -> dict[str, list[str]]:
    try:
        resolved_path = str(BASE_DIR / filepath)
        return load_skills_database(resolved_path)
    except Exception as exc:
        logger.warning("Failed loading skills database from %s: %s", filepath, exc)
        return load_skills_database()

def render_badge(label: str, badge_type: str = "neutral") -> str:
    schemes = {
        "matched": {"bg": "#d4edda", "text": "#155724", "border": "#c3e6cb", "p": "✓ "},
        "missing": {"bg": "#f8d7da", "text": "#721c24", "border": "#f5c6cb", "p": "✗ "},
        "additional": {"bg": "#cce5ff", "text": "#004085", "border": "#b8daff", "p": "+ "},
        "tech": {"bg": "#e7f1ff", "text": "#0c63e4", "border": "#b6d4fe", "p": ""},
        "soft": {"bg": "#f3e8fd", "text": "#6f42c1", "border": "#d8b4fe", "p": ""},
        "neutral": {"bg": "#e9ecef", "text": "#495057", "border": "#ced4da", "p": ""},
    }
    s = schemes.get(badge_type, schemes["neutral"])
    clean_label = label.replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<span style="display:inline-block; background-color:{s["bg"]}; color:{s["text"]}; '
        f'border:1px solid {s["border"]}; border-radius:14px; padding:3px 10px; margin:3px 3px; '
        f'font-size:12.5px; font-weight:500;">{s["p"]}{clean_label}</span>'
    )

def create_radar_chart(
    tfidf_score: float, semantic_score: float | None, skill_score: float
) -> go.Figure:
    sem_val = semantic_score if semantic_score is not None else 0.0
    categories = ["TF-IDF Lexical", "Semantic Context", "Skill Alignment"]
    values = [tfidf_score, sem_val, skill_score]

    fig = go.Figure(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(13, 110, 253, 0.22)",
            line=dict(color="#0d6efd", width=2.5),
            name="Match Dimensions",
            hovertemplate="%{theta}: <b>%{r:.1f}%</b><extra></extra>",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%", tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=12)),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        title=dict(text="<b>Match Dimensions (0 - 100%)</b>", x=0.5, font=dict(size=14)),
        margin=dict(l=35, r=35, t=45, b=25),
        height=300,
    )
    return fig

def create_skill_coverage_bar(
    matched_count: int, missing_count: int, additional_count: int
) -> go.Figure:
    categories = ["Matched Skills", "Missing Skills", "Additional Skills"]
    counts = [matched_count, missing_count, additional_count]
    colors = ["#28a745", "#dc3545", "#0d6efd"]

    fig = go.Figure(
        go.Bar(
            x=counts,
            y=categories,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(0,0,0,0.15)", width=1)),
            text=[f"{c} skill(s)" for c in counts],
            textposition="auto",
            hovertemplate="<b>%{y}</b>: %{x} skill(s)<extra></extra>",
        )
    )
    max_x = max(max(counts, default=1), 5)
    fig.update_layout(
        title=dict(text="<b>Skill Alignment Breakdown</b>", x=0.5, font=dict(size=14)),
        xaxis=dict(title="Count", tickformat="d", range=[0, max_x + 1]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=45, b=30),
        height=300,
    )
    return fig

def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "resume_text": "",
        "resume_filename": "",
        "resume_source_format": "",
        "resume_is_scanned": False,
        "candidate_info": None,
        "candidate_skills": [],
        "jd_text_input": "",
        "analyzed_jd": None,
        "edited_required_skills": "",
        "match_result": None,
        "sample_resume_loaded": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def render_sidebar() -> bool:
    st.sidebar.header("⚙️ Matching Configuration")
    use_semantic = st.sidebar.toggle(
        "Enable Semantic Matching",
        value=True,
        help="Uses Sentence Transformers to evaluate deep contextual and semantic equivalence.",
    )

    if use_semantic:
        st.sidebar.caption("🧠 Model: `sentence-transformers/all-MiniLM-L6-v2`")
        _ = load_cached_semantic_model()
    else:
        st.sidebar.caption("🔤 Semantic matching disabled (Lexical + Skill only)")

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ Scoring Formula Weights")
    if use_semantic:
        st.sidebar.markdown("- **Semantic Context:** 40%\n- **TF-IDF Lexical:** 30%\n- **Skill Match:** 30%")
    else:
        st.sidebar.markdown("- **TF-IDF Lexical:** 50%\n- **Skill Match:** 50%\n*(Semantic scoring disabled)*")

    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ About the Project")
    st.sidebar.markdown(
        "The system combines PDF/DOCX text extraction, rule-based entity parsing, "
        "TF-IDF n-gram vectorization, and neural semantic embeddings to objectively "
        "measure candidate-to-job requirement alignment."
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Privacy Notice")
    st.sidebar.info(
        "All resume parsing and scoring are performed strictly in-memory on your local instance. "
        "No candidate data, personal contact details, or job descriptions are transmitted externally."
    )
    return use_semantic

def render_header() -> None:
    st.title("🎯 AI-Powered Resume Parser & Job Matcher")
    st.markdown(
        "Upload a candidate resume (PDF/DOCX) and paste a target job description "
        "to extract structured profile details, detect core skills, and calculate "
        "context-aware match compatibility."
    )
    st.caption("⚠️ **Disclaimer:** This tool measures textual similarity and skill alignment. It does not predict hiring outcomes.")
    st.markdown("---")

def handle_resume_upload(skills_db: dict[str, list[str]]) -> None:
    st.subheader("📄 Resume Upload & Extraction")

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("📑 Load Sample Resume", use_container_width=True):
            sample_path = BASE_DIR / "sample_data" / "sample_resume.txt"
            if sample_path.is_file():
                try:
                    sample_text = sample_path.read_text(encoding="utf-8")
                    st.session_state["resume_text"] = sample_text
                    st.session_state["resume_filename"] = "sample_resume.txt"
                    st.session_state["resume_source_format"] = "txt"
                    st.session_state["resume_is_scanned"] = False
                    st.session_state["sample_resume_loaded"] = True

                    cand_info = extract_all(sample_text)
                    sk_res = extract_skills(sample_text, skills_db=skills_db)
                    all_skills = sk_res["technical_skills"] + sk_res["soft_skills"]
                    cand_info["skills"] = all_skills
                    st.session_state["candidate_info"] = cand_info
                    st.session_state["candidate_skills"] = all_skills
                    st.session_state["match_result"] = None
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to load sample resume: {exc}")
            else:
                st.error("Sample resume file not found at sample_data/sample_resume.txt")

    with col_info:
        if st.session_state.get("sample_resume_loaded"):
            st.info("Loaded **Sample Resume** (Arjun Sharma). Upload a file below to replace it.")

    uploaded_file = st.file_uploader(
        "Upload candidate resume (.pdf or .docx):",
        type=["pdf", "docx"],
        help="Upload a candidate resume in PDF or DOCX format (maximum size 10MB).",
        key="resume_file_uploader",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name

        is_valid, error_msg = validate_file(file_bytes, filename)
        if not is_valid:
            st.error(f"❌ File validation failed: {error_msg}")
        else:
            st.success(f"✅ File '{filename}' validated successfully ({len(file_bytes) / 1024:.1f} KB).")
            if (
                st.session_state.get("resume_filename") != filename
                or st.session_state.get("resume_bytes_len") != len(file_bytes)
            ):
                with st.spinner("Extracting text and metadata from resume..."):
                    try:
                        extracted = extract_text(file_bytes, filename)
                        extracted_text = extracted.get("text", "")
                        st.session_state["resume_text"] = extracted_text
                        st.session_state["resume_filename"] = filename
                        st.session_state["resume_source_format"] = extracted.get("source_format", "")
                        st.session_state["resume_is_scanned"] = extracted.get("is_scanned", False)
                        st.session_state["resume_bytes_len"] = len(file_bytes)
                        st.session_state["sample_resume_loaded"] = False

                        cand_info = extract_all(extracted_text)
                        sk_res = extract_skills(extracted_text, skills_db=skills_db)
                        all_skills = sk_res["technical_skills"] + sk_res["soft_skills"]
                        cand_info["skills"] = all_skills
                        st.session_state["candidate_info"] = cand_info
                        st.session_state["candidate_skills"] = all_skills
                        st.session_state["match_result"] = None
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to extract resume content: {exc}")

    if st.session_state.get("resume_is_scanned"):
        st.warning(
            "⚠️ **Scanned PDF Detected:** Low text density was detected. "
            "This document appears to be an image-only scan; OCR pre-processing is recommended."
        )

    current_resume_text = st.session_state.get("resume_text", "")
    if current_resume_text:
        with st.expander("📄 View Extracted Resume Plain Text"):
            st.text_area("Extracted Text", current_resume_text, height=180, disabled=True, key="raw_resume_preview")

def render_parsed_resume_info(skills_db: dict[str, list[str]]) -> None:
    candidate_info = st.session_state.get("candidate_info")
    resume_text = st.session_state.get("resume_text", "")
    if not candidate_info or not resume_text:
        st.info("Upload a resume or load the sample resume above to view parsed information.")
        return

    st.subheader("👤 Parsed Resume Information")
    col1, col2, col3 = st.columns(3)
    col1.metric("👤 Candidate Name", candidate_info.get("name") or "Not detected")
    col2.metric("📧 Email Address", candidate_info.get("email") or "Not detected")
    col3.metric("📞 Phone Number", candidate_info.get("phone") or "Not detected")

    st.markdown("#### 🎓 Education History")
    edu_list = candidate_info.get("education", [])
    if edu_list:
        df_edu = pd.DataFrame(edu_list).rename(columns={"degree": "Degree", "institution": "Institution", "year": "Year"})
        st.dataframe(df_edu, use_container_width=True, hide_index=True)
    else:
        st.caption("No structured education entries detected.")

    st.markdown("#### 💼 Professional Experience")
    exp_list = candidate_info.get("experience", [])
    if exp_list:
        df_exp = pd.DataFrame(exp_list).rename(columns={"title": "Job Title", "company": "Company", "duration": "Duration"})
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
    else:
        st.caption("No structured work experience entries detected.")

    st.markdown("#### 🛠️ Detected Candidate Skills")
    skills_extracted = extract_skills(resume_text, skills_db=skills_db)
    tech_skills = skills_extracted.get("technical_skills", [])
    soft_skills = skills_extracted.get("soft_skills", [])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(f"**Technical Skills ({len(tech_skills)}):**")
        st.markdown(" ".join(render_badge(s, "tech") for s in tech_skills) if tech_skills else "_None detected._", unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"**Soft Skills ({len(soft_skills)}):**")
        st.markdown(" ".join(render_badge(s, "soft") for s in soft_skills) if soft_skills else "_None detected._", unsafe_allow_html=True)

    col_c, col_p = st.columns(2)
    with col_c:
        st.markdown("#### 📜 Certifications")
        certs = candidate_info.get("certifications", [])
        st.markdown("\n".join(f"- {c}" for c in certs) if certs else "_No certifications identified._")
    with col_p:
        st.markdown("#### 🚀 Key Projects")
        projs = candidate_info.get("projects", [])
        st.markdown("\n".join(f"- {p}" for p in projs) if projs else "_No project entries identified._")

def handle_job_description_input(skills_db: dict[str, list[str]]) -> list[str]:
    st.subheader("💼 Job Description Input")

    col_sample, col_clear = st.columns([1, 1])
    with col_sample:
        if st.button("Load Sample JD", use_container_width=True):
            sample_jd_path = BASE_DIR / "sample_data" / "sample_job_description.txt"
            if sample_jd_path.is_file():
                try:
                    jd_content = sample_jd_path.read_text(encoding="utf-8")
                    st.session_state["jd_text_area"] = jd_content
                    st.session_state["jd_text_input"] = jd_content
                    st.session_state["edited_required_skills"] = ""
                    st.session_state["match_result"] = None
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to read sample job description: {exc}")
            else:
                st.error("Sample job description not found at sample_data/sample_job_description.txt")

    with col_clear:
        if st.button("🗑️ Clear JD", use_container_width=True):
            st.session_state["jd_text_area"] = ""
            st.session_state["jd_text_input"] = ""
            st.session_state["analyzed_jd"] = None
            st.session_state["edited_required_skills"] = ""
            st.session_state["match_result"] = None
            st.rerun()

    jd_text = st.text_area(
        "Paste Job Description (JD):",
        value=st.session_state.get("jd_text_input", ""),
        height=180,
        placeholder="Paste full job description text here, or click 'Load Sample JD' above...",
        key="jd_text_area",
    )
    st.session_state["jd_text_input"] = jd_text

    if not jd_text.strip():
        st.info("Paste a job description or click 'Load Sample JD' to extract requirements.")
        return []

    if (
        st.session_state.get("analyzed_jd") is None
        or st.session_state.get("analyzed_jd_raw_text") != jd_text
    ):
        with st.spinner("Analyzing job requirements, title, and qualifications..."):
            try:
                analyzed = analyze_job_description(jd_text, skills_db=skills_db)
                st.session_state["analyzed_jd"] = analyzed
                st.session_state["analyzed_jd_raw_text"] = jd_text
                st.session_state["edited_required_skills"] = ", ".join(analyzed.get("required_skills", []))
                st.session_state["match_result"] = None
            except Exception as exc:
                st.error(f"Failed to analyze job description: {exc}")
                return []

    analyzed_jd = st.session_state.get("analyzed_jd", {})
    st.markdown("#### 🎯 Analyzed Job Profile")
    col_t1, col_t2 = st.columns(2)
    col_t1.metric("🏢 Role Title", analyzed_jd.get("title") or "Not detected")
    col_t2.metric("⏳ Required Experience", analyzed_jd.get("experience_required") or "Not specified")

    req_skills = analyzed_jd.get("required_skills", [])
    pref_skills = analyzed_jd.get("preferred_skills", [])

    st.markdown(f"**Required Skills Detected ({len(req_skills)}):**")
    st.markdown(" ".join(render_badge(s, "tech") for s in req_skills) if req_skills else "_None detected._", unsafe_allow_html=True)

    st.markdown(f"**Preferred Skills ({len(pref_skills)}):**")
    st.markdown(" ".join(render_badge(s, "soft") for s in pref_skills) if pref_skills else "_None detected._", unsafe_allow_html=True)

    quals = analyzed_jd.get("qualifications", [])
    if quals:
        with st.expander("🎓 View Qualification Requirements"):
            for q in quals:
                st.markdown(f"- {q}")

    st.markdown("#### ✏️ Manual Skill Editing")
    current_edit_val = st.session_state.get("edited_required_skills", "")
    new_skills_input = st.text_input(
        "Customize Required Skills (comma-separated):",
        value=current_edit_val,
        help="Add or modify required skills to fine-tune matching expectations.",
        key="required_skills_editor_input",
    )

    if new_skills_input != current_edit_val:
        st.session_state["edited_required_skills"] = new_skills_input
        st.session_state["match_result"] = None

    return [s.strip() for s in new_skills_input.split(",") if s.strip()]

def render_match_analysis(
    resume_text: str,
    jd_text: str,
    candidate_skills: list[str],
    active_required_skills: list[str],
    use_semantic: bool,
) -> None:
    st.markdown("---")
    st.header("⚡ Match Analysis")

    if not resume_text.strip() or not jd_text.strip():
        st.info("👉 Please provide both a Resume and a Job Description above to perform match analysis.")
        return

    if st.button("🚀 Calculate Compatibility Score", type="primary", use_container_width=True):
        with st.spinner("Computing TF-IDF lexical, semantic embedding, and skill coverage match..."):
            try:
                result = compute_match(
                    resume_text=resume_text,
                    job_text=jd_text,
                    resume_skills=candidate_skills,
                    job_skills=active_required_skills,
                    use_semantic=use_semantic,
                )
                st.session_state["match_result"] = result
            except Exception as exc:
                st.error(f"Error computing candidate match: {exc}")
                return

    match_result = st.session_state.get("match_result")
    if not match_result:
        st.caption("Click 'Calculate Compatibility Score' above to evaluate profile alignment.")
        return

    overall_score = float(match_result.get("overall_score", 0.0))
    tfidf_score = float(match_result.get("tfidf_score", 0.0))
    semantic_score = match_result.get("semantic_score")
    skill_score = float(match_result.get("skill_match_score", 0.0))

    if overall_score >= 70.0:
        score_color = "#28a745"
        status_label = "🟢 Strong Alignment"
    elif overall_score >= 40.0:
        score_color = "#e0a800"
        status_label = "🟡 Moderate Alignment"
    else:
        score_color = "#dc3545"
        status_label = "🔴 Low Alignment"

    st.markdown(
        f"""
        <div style="background-color: {score_color}12; border: 1.5px solid {score_color}44;
                    border-radius: 12px; padding: 18px; text-align: center; margin: 15px 0;">
            <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px;
                        color: #6c757d; font-weight: 600;">Overall Match Score</div>
            <div style="color: {score_color}; font-size: 54px; font-weight: 800; line-height: 1.1; margin: 6px 0;">
                {overall_score:.1f}%
            </div>
            <div style="display: inline-block; background-color: {score_color}22; color: {score_color};
                        border-radius: 20px; padding: 3px 14px; font-weight: 600; font-size: 14px;">
                {status_label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, max(0.0, overall_score / 100.0)))

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("🔤 TF-IDF Score", f"{tfidf_score:.1f}%")
    col_m2.metric(
        "🧠 Semantic Score",
        f"{semantic_score:.1f}%" if semantic_score is not None else "Disabled / N/A",
    )
    col_m3.metric("🎯 Skill Match Score", f"{skill_score:.1f}%")

    st.markdown("#### 📊 Match Visualizations")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        radar_fig = create_radar_chart(tfidf_score, semantic_score, skill_score)
        st.plotly_chart(radar_fig, use_container_width=True)

    matched_skills = match_result.get("matched_skills", [])
    missing_skills = match_result.get("missing_skills", [])
    additional_skills = match_result.get("additional_skills", [])

    with col_c2:
        bar_fig = create_skill_coverage_bar(len(matched_skills), len(missing_skills), len(additional_skills))
        st.plotly_chart(bar_fig, use_container_width=True)

    st.markdown("#### 🏷️ Skills Breakdown")
    col_sk_m, col_sk_x, col_sk_a = st.columns(3)

    with col_sk_m:
        st.markdown(f"**Matched Skills ({len(matched_skills)}):**")
        st.markdown(" ".join(render_badge(s, "matched") for s in matched_skills) if matched_skills else "_None_", unsafe_allow_html=True)

    with col_sk_x:
        st.markdown(f"**Missing Skills ({len(missing_skills)}):**")
        st.markdown(" ".join(render_badge(s, "missing") for s in missing_skills) if missing_skills else "_None (Full coverage)_", unsafe_allow_html=True)

    with col_sk_a:
        st.markdown(f"**Additional Skills ({len(additional_skills)}):**")
        st.markdown(" ".join(render_badge(s, "additional") for s in additional_skills) if additional_skills else "_None_", unsafe_allow_html=True)

    st.markdown("#### 📝 Match Summary & Explanation")
    summary_text = generate_match_summary(match_result)
    st.info(f"**Match Summary:** {summary_text}")

    with st.expander("🔍 View Detailed Explanation"):
        st.write(match_result.get("explanation", "No detailed explanation available."))

def render_improvement_suggestions() -> None:
    match_result = st.session_state.get("match_result")
    if not match_result:
        return

    st.markdown("---")
    st.header("💡 Improvement Suggestions")
    suggestions = generate_improvement_suggestions(match_result)

    if suggestions:
        for idx, suggestion in enumerate(suggestions, start=1):
            st.markdown(f"**{idx}.** {suggestion}")
    else:
        st.caption("Candidate exhibits high coverage across evaluated criteria.")

def render_report_export(
    candidate_info: dict[str, Any] | None, analyzed_jd: dict[str, Any] | None
) -> None:
    match_result = st.session_state.get("match_result")
    if not match_result:
        return

    st.markdown("---")
    st.header("📥 Report Export")

    job_title = (analyzed_jd or {}).get("title", "")
    safe_info = candidate_info or {}
    cand_name = safe_info.get("name") or "Candidate"
    safe_filename = re.sub(r"[^a-zA-Z0-9_\-]", "_", cand_name).strip("_") or "candidate"

    json_report = generate_json_report(safe_info, match_result, job_title=job_title)
    csv_report = generate_csv_report(safe_info, match_result, job_title=job_title)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📄 Download JSON Report",
            data=json_report,
            file_name=f"{safe_filename}_match_report.json",
            mime="application/json",
            use_container_width=True,
            key="dl_json_report",
        )

    with col_dl2:
        st.download_button(
            label="📊 Download CSV Report",
            data=csv_report,
            file_name=f"{safe_filename}_match_report.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv_report",
        )

def main() -> None:
    st.set_page_config(
        page_title="AI-Powered Resume Parser & Job Matcher",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    skills_db = get_cached_skills_db()
    use_semantic = render_sidebar()
    render_header()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        handle_resume_upload(skills_db)
        st.markdown("---")
        render_parsed_resume_info(skills_db)

    with col_right:
        active_required_skills = handle_job_description_input(skills_db)

    resume_text = st.session_state.get("resume_text", "")
    jd_text = st.session_state.get("jd_text_input", "")
    candidate_skills = st.session_state.get("candidate_skills", [])

    render_match_analysis(
        resume_text=resume_text,
        jd_text=jd_text,
        candidate_skills=candidate_skills,
        active_required_skills=active_required_skills,
        use_semantic=use_semantic,
    )

    render_improvement_suggestions()
    render_report_export(
        candidate_info=st.session_state.get("candidate_info"),
        analyzed_jd=st.session_state.get("analyzed_jd"),
    )

if __name__ == "__main__":
    main()
