# Testing Report

## Testing Methodology

The verification strategy for the **AI-Powered Resume Parser and Job Matching System** relies on automated unit and integration testing orchestrated through `pytest`. The testing suite is built on the following engineering principles:

1. **Synthetic In-Memory Data Generation**:
   - Rather than relying on static external binary files that can become corrupted or deleted, the test suite constructs valid PDF documents dynamically in-memory using [`PyMuPDF (fitz)`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/tests/test_resume_extractor.py#L22-L37) and valid Microsoft Word documents dynamically using [`python-docx`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/tests/test_resume_extractor.py#L39-L53).
   - This guarantees 100% reproducible test artifacts across disparate CI/CD and developer environments.
2. **Deterministic Assertions & Edge-Case Probing**:
   - Every module is subjected to boundary conditions, including zero-length inputs, malformed unicode characters, arbitrary whitespace strings, corrupt byte streams, and oversized payload limits.
3. **Isolated Component Verification**:
   - Text preprocessing, regex matching, heuristic section chunking, and similarity math are validated in isolation to pinpoint regressions without confounding cross-module dependencies.
4. **Graceful Fallback Validation**:
   - The test suite verifies that when neural sentence transformer libraries or GPU accelerators are unavailable, the matching engine falls back seamlessly to lexical and skill scoring without crashing.

---

## Test Environment

The test suite was executed and verified under the following standardized baseline configuration:

| Specification Parameter | Environment Value |
| :--- | :--- |
| **Operating System** | Microsoft Windows 10 / Windows 11 (x64) |
| **Python Runtime** | Python 3.11.x (64-bit) |
| **Test Framework** | `pytest 8.3.3` (with pluggy 1.6.0) |
| **Document Processing Libraries** | `PyMuPDF (fitz) 1.24.10`, `python-docx 1.1.2` |
| **Machine Learning & NLP** | `scikit-learn 1.5.2`, `sentence-transformers 3.1.1`, `numpy 1.26.4` |
| **Data & Report Formats** | Standard Library `io`, `json`, `csv`, `re` |

---

## Test Categories

The test suite is structured across two primary testing categories:

1. **Unit Tests**:
   - **File Validation & Document Parsing**: Ensures that [`validate_file`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_extractor.py#L202-L246) correctly enforces extension whitelisting, file size restrictions, and non-empty byte streams.
   - **Entity Extraction**: Validates regex extraction routines in [`information_extractor.py`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/information_extractor.py) for email formats, international phone formats, candidate names, academic histories, employment periods, certifications, and technical projects.
   - **Skill Taxonomy Matching**: Validates [`match_skills_to_requirements`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/skill_extractor.py#L200-L264) for exact, partial, and zero-match scenarios with case and whitespace normalization.
   - **Similarity Math**: Asserts that [`tfidf_similarity`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L39-L66) and [`semantic_similarity`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L92-L125) properly bound outputs between `0.0` and `1.0`.
2. **Integration Tests**:
   - **Document Ingestion Pipeline**: Asserts that [`extract_text`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_extractor.py#L161-L200) dispatches transparently between PDF and DOCX handlers and delivers clean text with metadata.
   - **Composite Match Pipeline**: Validates [`compute_match`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/resume_matcher.py#L127-L248) under both semantic-enabled and semantic-disabled configurations.
   - **Report Serialization**: Validates that [`generate_json_report`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/report_generator.py#L162-L191) and [`generate_csv_report`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/src/report_generator.py#L193-L266) produce schema-compliant payloads.

---

## Test Cases

Below is the complete matrix of 46 automated test cases spanning all test modules in the repository:

### 1. Resume Extractor Module ([`tests/test_resume_extractor.py`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/tests/test_resume_extractor.py))

| Test ID | Module | Test Name | Description | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-RE-01` | `resume_extractor` | `test_validate_file_valid_pdf` | Validate that a non-empty `.pdf` file passes validation. | Returns `(True, "")` | Verified |
| `TC-RE-02` | `resume_extractor` | `test_validate_file_valid_docx` | Validate that a non-empty `.docx` file passes validation. | Returns `(True, "")` | Verified |
| `TC-RE-03` | `resume_extractor` | `test_validate_file_empty` | Validate that empty byte payload fails validation with error message. | Returns `(False, "File is empty.")` | Verified |
| `TC-RE-04` | `resume_extractor` | `test_validate_file_unsupported_extension` | Validate that unsupported file extensions (`.txt`, `.png`) fail validation. | Returns `(False, msg)` with "unsupported" | Verified |
| `TC-RE-05` | `resume_extractor` | `test_validate_file_too_large` | Validate that payload exceeding `max_size_mb` threshold fails validation. | Returns `(False, msg)` with "exceeds" | Verified |
| `TC-RE-06` | `resume_extractor` | `test_validate_file_no_extension` | Validate that filenames without extensions or empty filenames fail validation. | Returns `(False, msg)` with "extension" | Verified |
| `TC-RE-07` | `resume_extractor` | `test_extract_text_unsupported_format` | Validate that `extract_text` raises `ValueError` on unsupported or missing extensions. | Raises `ValueError` | Verified |
| `TC-RE-08` | `resume_extractor` | `test_extract_text_from_pdf_empty` | Validate that `extract_text_from_pdf` raises `ValueError` when input bytes are empty. | Raises `ValueError` containing "empty" | Verified |
| `TC-RE-09` | `resume_extractor` | `test_extract_text_from_docx_empty` | Validate that `extract_text_from_docx` raises `ValueError` when input bytes are empty. | Raises `ValueError` containing "empty" | Verified |
| `TC-RE-10` | `resume_extractor` | `test_extract_text_dispatches_pdf` | Validate that `extract_text` dispatches to PDF extractor and extracts text from in-memory PDF. | Returns dict with `source_format="pdf"`, `num_pages=1`, text | Verified |
| `TC-RE-11` | `resume_extractor` | `test_extract_text_dispatches_docx` | Validate that `extract_text` dispatches to DOCX extractor and extracts text from in-memory DOCX. | Returns dict with `source_format="docx"`, `num_paragraphs>=1`, text | Verified |
| `TC-RE-12` | `resume_extractor` | `test_extract_text_from_pdf_corrupt` | Validate that corrupted byte streams passed to `extract_text_from_pdf` raise `ValueError`. | Raises `ValueError` containing "failed to open pdf document" | Verified |
| `TC-RE-13` | `resume_extractor` | `test_extract_text_from_docx_corrupt` | Validate that corrupted byte streams passed to `extract_text_from_docx` raise `ValueError`. | Raises `ValueError` containing "failed to open docx document" | Verified |

---

### 2. Information Extractor Module ([`tests/test_information_extractor.py`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/tests/test_information_extractor.py))

| Test ID | Module | Test Name | Description | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-IE-01` | `information_extractor` | `test_extract_email_found` | Validate extraction of an RFC-compliant email address when present in resume text. | Returns `"alex.smith@example.org"` | Verified |
| `TC-IE-02` | `information_extractor` | `test_extract_email_not_found` | Validate fallback return value when no email address is present in text. | Returns `"Not found"` | Verified |
| `TC-IE-03` | `information_extractor` | `test_extract_email_multiple` | Validate that the first email address is returned when multiple addresses exist. | Returns `"primary.dev@domain.com"` | Verified |
| `TC-IE-04` | `information_extractor` | `test_extract_phone_found_indian` | Validate extraction of Indian phone numbers (`+91-9876543210` and `9876543210`). | Returns string containing `"9876543210"` | Verified |
| `TC-IE-05` | `information_extractor` | `test_extract_phone_found_us` | Validate extraction of standard US phone formats (`555-123-4567` and `(555) 234-5678`). | Returns correctly matched US phone number | Verified |
| `TC-IE-06` | `information_extractor` | `test_extract_phone_not_found` | Validate fallback return value when no valid telephone number is listed. | Returns `"Not found"` | Verified |
| `TC-IE-07` | `information_extractor` | `test_extract_name_found` | Validate extraction of candidate name from top header rows of resume. | Returns `"Arjun Sharma"` and `"Priya Sundaram"` | Verified |
| `TC-IE-08` | `information_extractor` | `test_extract_name_not_found` | Validate fallback return value when no recognizable name is present or text is empty. | Returns `"Not found"` | Verified |
| `TC-IE-09` | `information_extractor` | `test_extract_education_found` | Validate extraction of academic degree, institution, and graduation span. | Returns list of dicts with `degree`, `institution`, `year` | Verified |
| `TC-IE-10` | `information_extractor` | `test_extract_education_not_found` | Validate that empty list is returned when education details are absent or text is empty. | Returns `[]` | Verified |
| `TC-IE-11` | `information_extractor` | `test_extract_experience_found` | Validate extraction of professional experience entries (title, company, duration). | Returns list of dicts with `title`, `company`, `duration` | Verified |
| `TC-IE-12` | `information_extractor` | `test_extract_experience_not_found` | Validate that empty list is returned when work experience is absent or text is empty. | Returns `[]` | Verified |
| `TC-IE-13` | `information_extractor` | `test_extract_certifications_found` | Validate extraction of listed industry certifications. | Returns list containing AWS and Google certificate names | Verified |
| `TC-IE-14` | `information_extractor` | `test_extract_certifications_not_found` | Validate that empty list is returned when certifications are absent or text is empty. | Returns `[]` | Verified |
| `TC-IE-15` | `information_extractor` | `test_extract_projects_found` | Validate extraction of technical project headline entries. | Returns list containing `"E-Commerce Platform"` and `"Chat Application"` | Verified |
| `TC-IE-16` | `information_extractor` | `test_extract_projects_not_found` | Validate that empty list is returned when project entries are absent or text is empty. | Returns `[]` | Verified |
| `TC-IE-17` | `information_extractor` | `test_extract_all_complete` | Validate consolidated entity extraction containing all expected structured fields. | Returns dict with all 7 keys populated (`name`, `email`, `phone`, `education`, `experience`, `certifications`, `projects`) | Verified |
| `TC-IE-18` | `information_extractor` | `test_extract_all_empty_text` | Validate that `extract_all` gracefully handles empty or whitespace input. | Returns default dict with `"Not found"` and empty lists | Verified |

---

### 3. Resume Matcher, Skill Matcher & Report Generator ([`tests/test_resume_matcher.py`](file:///c:/Users/omkal/Documents/antigravity/dazzling-hypatia/tests/test_resume_matcher.py))

| Test ID | Module | Test Name | Description | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-RM-01` | `resume_matcher` | `test_tfidf_similarity_identical` | Validate that identical texts produce maximum cosine similarity. | `score ≈ 1.0` (within tolerance `1e-3`) | Verified |
| `TC-RM-02` | `resume_matcher` | `test_tfidf_similarity_different` | Validate that completely disjoint texts produce near-zero cosine similarity. | `score < 0.05` | Verified |
| `TC-RM-03` | `resume_matcher` | `test_tfidf_similarity_empty` | Validate that empty strings, whitespace, or pure symbols produce `0.0`. | Returns `0.0` | Verified |
| `TC-RM-04` | `resume_matcher` | `test_tfidf_similarity_partial_overlap` | Validate that partially overlapping texts produce intermediate similarity scores. | `0.1 < score < 0.95` | Verified |
| `TC-RM-05` | `resume_matcher` | `test_semantic_similarity` | Validate semantic cosine similarity for conceptually related sentences using Sentence Transformers. | `score > 0.5` bounded in `[0.0, 1.0]`; `0.0` on empty | Verified |
| `TC-RM-06` | `resume_matcher` | `test_compute_match_without_semantic` | Validate `compute_match` execution when semantic matching is disabled. | Dict with `semantic_score=None`, overall score = `0.5*tfidf + 0.5*skill_match` | Verified |
| `TC-RM-07` | `resume_matcher` | `test_compute_match_score_range` | Validate that all scores returned by `compute_match` remain bounded within `[0.0, 100.0]`. | All scores bounded in `[0.0, 100.0]` | Verified |
| `TC-RM-08` | `resume_matcher` | `test_compute_match_skills` | Validate skill breakdown partitioning (`matched`, `missing`, `additional`) and percentage calculation. | Matched: Python, Docker; Missing: Kubernetes, AWS; Score: `50.0%` | Verified |
| `TC-RM-09` | `resume_matcher` | `test_compute_match_empty_skills` | Validate `compute_match` when both candidate and job have empty skill lists. | Empty skill arrays; `skill_match_score=100.0`; valid overall score | Verified |
| `TC-SK-01` | `skill_extractor` | `test_skill_matching_all_matched` | Validate `match_skills_to_requirements` when candidate possesses all required skills. | `match_percentage = 100.0%`, `missing = []`, correct `additional` | Verified |
| `TC-SK-02` | `skill_extractor` | `test_skill_matching_none_matched` | Validate `match_skills_to_requirements` when candidate has none of the required skills. | `match_percentage = 0.0%`, all required skills in `missing` | Verified |
| `TC-SK-03` | `skill_extractor` | `test_skill_matching_partial` | Validate `match_skills_to_requirements` with partial match and case normalization. | `match_percentage = 50.0%` (Python, C++ matched; Angular, Vue.js missing) | Verified |
| `TC-RG-01` | `report_generator` | `test_generate_json_report_valid` | Validate schema structure and formatting of `generate_json_report`. | Returns valid JSON string parseable into dictionary with all required keys and ≥5 suggestions | Verified |
| `TC-RG-02` | `report_generator` | `test_generate_csv_report_valid` | Validate formatting, headers, and key metrics in `generate_csv_report`. | Returns valid CSV string containing header `Category,Metric / Field,Value` and candidate metrics | Verified |
| `TC-RG-03` | `report_generator` | `test_generate_improvement_suggestions` | Validate `generate_improvement_suggestions` produces 5–10 targeted suggestions. | Returns list of 5–10 descriptive strings addressing missing skills and score gaps | Verified |

---

## Running Tests

Execute the automated test suite using the following command variations depending on your objective:

### 1. Run Complete Test Suite Verbose
```bash
pytest tests/ -v
```

### 2. Run Individual Test Modules
To isolate testing to specific system layers:

```bash
# Test Document Extraction & File Validation Layer
pytest tests/test_resume_extractor.py -v

# Test Entity Extraction & Section Parsing Layer
pytest tests/test_information_extractor.py -v

# Test Hybrid Matching, Skill Coverage & Report Generation
pytest tests/test_resume_matcher.py -v
```

### 3. Run with Execution Timing Profiling
Identify execution latency bottlenecks across individual test cases:
```bash
pytest tests/ -v --durations=10
```

### 4. Run with Code Coverage Report
To measure line and branch coverage across the `src/` package (requires `pytest-cov`):
```bash
pytest --cov=src tests/ --cov-report=term-missing --cov-report=html
```

---

## Coverage

The testing suite emphasizes thorough coverage across core domain logic:

- **Branch Coverage**:
  - File extension validation branches (`.pdf`, `.docx`, unsupported, missing extensions).
  - Format dispatcher routing in `extract_text`.
  - Section header recognizer regex variations across `education`, `experience`, `certifications`, `projects`, and `skills`.
  - Dual scoring pathways in `compute_match` (semantic enabled vs. semantic disabled fallback).
- **Boundary Condition Testing**:
  - Zero-length strings, empty byte buffers (`b""`), single-word lines, and whitespace-only payloads.
  - Zero-skill requirement job descriptions (confirming default `100.0%` requirement coverage).
  - Score clamping assertions verifying outputs never exceed `100.0%` or dip below `0.0%`.
- **Exception & Fault Tolerance Verification**:
  - Asserting `ValueError` on corrupt PDF byte headers and malformed DOCX zip archives.
  - Asserting graceful fallback to `"Not found"` for missing candidate identifiers.
  - Graceful fallback when the external `sentence-transformers` library or model weights are missing.

---

## Known Issues

The following known architectural and environmental testing limitations are acknowledged:

1. **Scanned PDF Optical Character Recognition (OCR)**:
   - The current `extract_text_from_pdf` module utilizes heuristic page character density (`avg_chars < 30`) to flag documents as scanned (`is_scanned=True`). OCR text extraction via Tesseract or cloud vision APIs is not implemented in the base pipeline, so image-based resumes return empty text bodies.
2. **Multi-Column PDF Reading Order**:
   - Resumes formatted with intricate multi-column tabular layouts may experience text interleaving when parsed via standard PyMuPDF `page.get_text()`. The heuristics use section-boundary regex to mitigate cross-column contamination, but highly stylized resumes may require coordinate-based sorting.
3. **First-Run Sentence Transformer Initialization**:
   - `test_semantic_similarity` downloads the 90 MB `all-MiniLM-L6-v2` checkpoint on its initial execution. In restricted air-gapped environments without pre-cached Hugging Face weights, this test is skipped via `@pytest.mark.skipif(not HAS_ST, ...)`.
4. **Python Version Compatibility**:
   - The deep learning backend dependencies (`torch 2.4.1` and `sentence-transformers 3.1.1`) are validated on Python 3.11. Executing tests under unreleased or bleeding-edge runtimes (such as Python 3.14+) may trigger third-party dependency warnings or C-extension incompatibilities.
