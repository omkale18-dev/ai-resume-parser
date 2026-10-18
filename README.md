# 🎯 AI-Powered Resume Parser & Job Matching System

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit%201.38.0-red.svg)](https://streamlit.io/)
[![Deep Learning](https://img.shields.io/badge/embeddings-sentence--transformers%203.1.1-yellow.svg)](https://www.sbert.net/)
[![Machine Learning](https://img.shields.io/badge/ML-scikit--learn%201.5.2-orange.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-pytest%208.3.3-brightgreen.svg)](https://pytest.org/)

An enterprise-grade, privacy-first NLP system that parses unstructured resume documents (PDF and DOCX) and accurately matches candidate qualifications against job descriptions. The system leverages an in-memory streaming extraction engine combined with a hybrid scoring pipeline that synthesizes TF-IDF lexical frequency, deep Sentence Transformer semantic embeddings (`all-MiniLM-L6-v2`), and exact skill taxonomy coverage. Built with high-throughput heuristics and modular Python components, it provides recruiters and candidates with immediate, explainable fit assessments via an interactive Streamlit web dashboard.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Usage Guide](#-usage-guide)
- [Running Tests](#-running-tests)
- [Configuration](#-configuration)
- [Privacy & Ethics](#-privacy--ethics)
- [Limitations](#-limitations)
- [License](#-license)
- [Contributors](#-contributors)

---

## 🌟 Overview

The **AI-Powered Resume Parser & Job Matching System** automates the labor-intensive recruitment screening process by transforming unstructured resumes into structured analytical data profiles. Operating entirely locally in-memory without transmitting sensitive candidate information to third-party cloud APIs, the system extracts critical identifiers including candidate names, contact details, education histories, work experience, certifications, and technical proficiencies. Extracted candidate attributes are evaluated against job requirements using a weighted three-pillar match algorithm: lexical term frequency (TF-IDF), dense contextual semantics (Sentence Transformers), and deterministic domain taxonomy alignment. The resulting analytics provide recruiter-facing dashboards with granular match scores, identified skill gaps, candidate strengths, and structured export capabilities.

---

## ✨ Features

- **Multi-Format In-Memory Document Ingestion**:
  - High-performance PDF parsing using [PyMuPDF (fitz)](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_extractor.py#L15-L75) with scanned document heuristic detection.
  - Comprehensive DOCX parsing with table-structure preservation using [python-docx](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_extractor.py#L77-L159).
  - Pure in-memory streaming pipeline without disk persistence of uploaded files for guaranteed privacy.
  - Rigorous file validation checking MIME integrity, extension whitelist (`.pdf`, `.docx`), and configurable file size limits (default 10 MB) via [`validate_file`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_extractor.py#L202-L245).

- **Robust Text Preprocessing Pipeline**:
  - Unicode normalization (NFKD decomposition) and whitespace collapsing via [`normalize_text`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/text_preprocessor.py#L236-L255).
  - Punctuation cleaning preserving emails, phone numbers, and programming symbols (`C++`, `.NET`, `C#`) via [`clean_text`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/text_preprocessor.py#L257-L280).
  - Abbreviation-aware sentence segmentation safeguarding honorifics, degrees, and corporate prefixes via [`segment_sentences`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/text_preprocessor.py#L282-L327).
  - Independent token pipelines specialized for TF-IDF vectorization ([`preprocess_for_tfidf`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/text_preprocessor.py#L375-L400)) and semantic dense embeddings ([`preprocess_for_embedding`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/text_preprocessor.py#L402-L424)).

- **Intelligent Information Extraction**:
  - Accurate candidate name extraction through structural header heuristics avoiding noise tokens via [`extract_name`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L434-L502).
  - International and domestic phone number detection across US, Indian, and international standards via [`extract_phone`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L404-L432).
  - RFC 5322-compliant email parsing via [`extract_email`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L380-L402).
  - Structured education extraction capturing degree qualifications, educational institutions, and graduation graduation year ranges via [`extract_education`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L504-L625).
  - Work history extraction identifying job titles, employer organizations, and duration tenures via [`extract_experience`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L627-L744).
  - Industry certifications and project cataloging via [`extract_certifications`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L746-L800) and [`extract_projects`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py#L802-L847).

- **Dynamic Skill Taxonomy & Matching**:
  - Over 200+ pre-configured technical and soft skills cataloged in [skills.json](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/data/skills.json) loaded via [`load_skills_database`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/skill_extractor.py#L56-L113).
  - Boundary-aware regex compiler handling technical tokens (e.g., `C++`, `C#`, `.NET`, `Go`, `Node.js`) without false positive substrings via [`_compile_skill_pattern`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/skill_extractor.py#L115-L147).
  - Deterministic skill-to-requirement comparison classifying skills into `matched`, `missing`, and `additional` sets via [`match_skills_to_requirements`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/skill_extractor.py#L200-L264).

- **Three-Pillar Hybrid Matching Engine**:
  - **TF-IDF Lexical Cosine Similarity** (30% weight) via [`tfidf_similarity`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L39-L66).
  - **Sentence Transformer Semantic Similarity** (40% weight) utilizing `all-MiniLM-L6-v2` via [`semantic_similarity`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L92-L125).
  - **Skill Requirement Coverage** (30% weight) measuring exact match percentage.
  - Automatic fault-tolerant fallback (50% TF-IDF + 50% Skill Match) when deep learning dependencies or accelerators are unavailable.
  - Transparent human-readable analytical explanations generated via [`compute_match`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L127-L248).

- **Interactive User Interface & Reporting**:
  - Responsive web dashboard built with Streamlit and Plotly charts.
  - Real-time gauge meters and breakdown visualizations.
  - Downloadable candidate evaluation reports.

---

## 🛠 Tech Stack

| Technology | Purpose | Version |
| :--- | :--- | :--- |
| **Python** | Primary programming language | `3.11+` |
| **Streamlit** | Interactive web application framework & user dashboard | `1.38.0` |
| **PyMuPDF (fitz)** | High-speed, memory-efficient PDF text and metadata extraction | `1.24.10` |
| **python-docx** | Microsoft Word (.docx) document parsing and table reading | `1.1.2` |
| **NLTK** | Natural Language Processing tokenization and linguistic stopword corpora | `3.9.1` |
| **spaCy** | Advanced linguistic preprocessing and entity token structures | `3.7.6` |
| **Sentence-Transformers** | Dense semantic embedding generation (`all-MiniLM-L6-v2`) | `3.1.1` |
| **scikit-learn** | Machine learning utilities, TF-IDF vectorization, cosine similarity | `1.5.2` |
| **pandas** | Tabular data processing and candidate report generation | `2.2.3` |
| **NumPy** | High-performance numerical and tensor operations | `1.26.4` |
| **PyTorch (torch)** | Deep learning CPU/GPU compute backend for transformer models | `2.4.1` |
| **Plotly** | Interactive visualization (radar charts, gauge meters, skill bars) | `5.24.1` |
| **chardet** | Character encoding detection for raw document streams | `5.2.0` |
| **pytest** | Automated test suite and test execution framework | `8.3.3` |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher installed on your operating system.
- Git version control.

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd resume-parser-project

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (if needed)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Run the application
streamlit run app.py
```

Upon launching, navigate to `http://localhost:8501` in your web browser to access the dashboard.

---

## 📁 Project Structure

```text
dazzling-hypatia/
├── .gitignore                      # Git ignored files and directories
├── README.md                       # Comprehensive project documentation
├── requirements.txt                # Pinned production dependencies
├── app.py                          # Streamlit web application entrypoint
├── data/
│   └── skills.json                 # Standardized technical & soft skill taxonomy
├── docs/
│   ├── architecture.md             # System architecture & interface specifications
│   ├── user_manual.md              # End-user operation & troubleshooting manual
│   └── testing_report.md           # Test methodology, test matrix & verification
├── src/
│   ├── __init__.py                 # Core package initializer
│   ├── resume_extractor.py         # PDF and DOCX text & metadata extractors
│   ├── text_preprocessor.py        # Text cleaning, normalization & segmentation
│   ├── information_extractor.py    # Regex & heuristic entity extraction engine
│   ├── skill_extractor.py          # Taxonomy loading, regex compiler & skill matcher
│   └── resume_matcher.py           # TF-IDF, Semantic embeddings & hybrid score engine
└── tests/
    ├── __init__.py                 # Test package initializer
    ├── conftest.py                 # Pytest shared fixtures & test setup
    ├── test_resume_extractor.py    # Tests for document ingestion & validation
    ├── test_information_extractor.py # Tests for entity & section extraction
    └── test_resume_matcher.py      # Tests for similarity & scoring algorithms
```

---

## 📖 Usage Guide

1. **Upload Resume**:
   - In the Streamlit application sidebar or main panel, click **"Browse files"** or drag and drop a candidate resume (`.pdf` or `.docx`).
   - The file validation layer validates extension integrity and confirms file size is within the allowed limit (10 MB).
2. **Review Extracted Information**:
   - Inspect parsed candidate demographics (Name, Email, Phone).
   - Review structured sections: Education qualifications, Professional Experience history, Certifications, and Projects.
   - View extracted Technical and Soft skills detected against the taxonomy.
3. **Provide Job Description**:
   - Paste the target job posting or role description into the designated text area.
   - The system automatically extracts required competencies from the job description.
4. **Execute Match Analysis**:
   - Click **"Analyze Match"** to trigger the hybrid calculation engine.
   - Review the aggregate **Overall Match Score** (0–100%) and individual component weights (TF-IDF Lexical, Sentence Transformer Semantic, and Skill Coverage).
   - Check the **Skill Gap Analysis** to see Confirmed Skills, Missing Requirements, and Additional Candidate Strengths.
5. **Export Evaluation Report**:
   - Generate and download a formatted report (PDF / Markdown / JSON) containing complete parsed details and match evaluations for hiring panels.

---

## 🧪 Running Tests

The test suite validates document parsing, text preprocessing, heuristic information extraction, skill compilation, and hybrid matching algorithms.

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run tests with execution timing summary
pytest tests/ -v --durations=10

# Run a specific test module
pytest tests/test_information_extractor.py -v

# Run with test coverage report (if pytest-cov installed)
pytest --cov=src tests/ --cov-report=term-missing
```

---

## ⚙️ Configuration

### Extending Skills Taxonomy
The skill catalog is located at [data/skills.json](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/data/skills.json). To add new domain-specific tools or soft skills, append entries into the respective list:

```json
{
  "technical_skills": [
    "Python",
    "Kubernetes",
    "YourCustomFramework"
  ],
  "soft_skills": [
    "Leadership",
    "Negotiation",
    "YourDomainSkill"
  ]
}
```
The regex engine automatically handles word boundary compilation and casing invariance on next run without requiring application restarts.

### Adjusting Match Weights
Matching weights can be tuned in [src/resume_matcher.py](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L192-L197):

```python
# Default configuration:
# 30% TF-IDF, 40% Semantic Embeddings, 30% Skill Coverage
raw_overall = (0.3 * tfidf_score) + (0.4 * semantic_score) + (0.3 * skill_match_score)
```

---

## 🔒 Privacy & Ethics

- **Zero Cloud Transmission**: All document extraction, text parsing, embedding generation, and scoring computations execute entirely on local compute infrastructure. No resume content is sent to third-party generative APIs or external hosted endpoints.
- **In-Memory Streaming**: Documents are ingested as in-memory byte streams (`io.BytesIO`) and discarded after processing. No applicant data or uploaded files are persisted to local disk storage unless explicitly exported by the user.
- **Fairness & Bias Mitigation**: The scoring algorithm evaluates candidate qualifications solely on verifiable linguistic evidence, validated skills, and contextual experience descriptions. Demographic identifiers (e.g., gender, race, age, address) are explicitly excluded from mathematical match weight computations.

---

## ⚠️ Limitations

- **Scanned / Image-Based PDFs**: The system includes a heuristic scanner detector (flagging documents with fewer than 30 characters per page). Pure image scans require an OCR pre-processing step (such as Tesseract OCR) to extract raw text prior to ingestion.
- **Complex Multi-Column Tables**: While standard Word tables and single/double column layouts are handled, heavily nested or non-standard graphic resumes may require manual verification of reading order.
- **Language Scope**: The current text preprocessor and skill database are optimized for English-language resumes. Non-English resumes may require additional stopword corpora and localized skill dictionaries.
- **Model Initialization**: On initial execution, the `all-MiniLM-L6-v2` Sentence Transformer weights (~80 MB) are downloaded once to local cache. Ensure active internet connectivity during the first run.

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 👥 Contributors

- **Om K.** - *Lead System Architect & NLP Developer* (placeholder)
- Open source community contributors welcome!
