import re
import unicodedata

ENGLISH_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "about",
        "above",
        "after",
        "again",
        "against",
        "ain",
        "all",
        "am",
        "an",
        "and",
        "any",
        "are",
        "aren",
        "aren't",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "below",
        "between",
        "both",
        "but",
        "by",
        "can",
        "couldn",
        "couldn't",
        "d",
        "did",
        "didn",
        "didn't",
        "do",
        "does",
        "doesn",
        "doesn't",
        "doing",
        "don",
        "don't",
        "down",
        "during",
        "each",
        "few",
        "for",
        "from",
        "further",
        "had",
        "hadn",
        "hadn't",
        "has",
        "hasn",
        "hasn't",
        "have",
        "haven",
        "haven't",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "isn",
        "isn't",
        "it",
        "it's",
        "its",
        "itself",
        "just",
        "ll",
        "m",
        "ma",
        "me",
        "mightn",
        "mightn't",
        "more",
        "most",
        "mustn",
        "mustn't",
        "my",
        "myself",
        "needn",
        "needn't",
        "no",
        "nor",
        "not",
        "now",
        "o",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "other",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "re",
        "s",
        "same",
        "shan",
        "shan't",
        "she",
        "she's",
        "should",
        "should've",
        "shouldn",
        "shouldn't",
        "so",
        "some",
        "such",
        "t",
        "than",
        "that",
        "that'll",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "ve",
        "very",
        "was",
        "wasn",
        "wasn't",
        "we",
        "were",
        "weren",
        "weren't",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "whom",
        "why",
        "will",
        "with",
        "won",
        "won't",
        "wouldn",
        "wouldn't",
        "y",
        "you",
        "you'd",
        "you'll",
        "you're",
        "you've",
        "your",
        "yours",
        "yourself",
        "yourselves",
    }
)

_ABBREVIATION_PATTERNS: list[str] = [
    r"\bDr\.",
    r"\bMr\.",
    r"\bMrs\.",
    r"\bMs\.",
    r"\bProf\.",
    r"\bSr\.",
    r"\bJr\.",
    r"\bRev\.",
    r"\bHon\.",
    r"\be\.g\.",
    r"\bi\.e\.",
    r"\betc\.",
    r"\bvs\.",
    r"\bal\.",
    r"\bInc\.",
    r"\bLtd\.",
    r"\bCorp\.",
    r"\bCo\.",
    r"\bDept\.",
    r"\bEst\.",
    r"\bApprox\.",
    r"\bApt\.",
    r"\bPh\.D\.",
    r"\bM\.D\.",
    r"\bB\.Tech\.",
    r"\bM\.Tech\.",
    r"\bB\.Sc\.",
    r"\bM\.Sc\.",
    r"\bB\.A\.",
    r"\bM\.A\.",
    r"\bB\.E\.",
    r"\bM\.E\.",
    r"\bB\.S\.",
    r"\bM\.S\.",
    r"\b[A-Z]\.",
]

def normalize_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    normalized = unicodedata.normalize("NFKD", text)
    return re.sub(r"\s+", " ", normalized).strip()

def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    cleaned = re.sub(r"[^a-zA-Z0-9\s.,@+\-]", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()

def segment_sentences(text: str) -> list[str]:
    if not text or not isinstance(text, str):
        return []

    stripped = text.strip()
    if not stripped:
        return []

    placeholder = "@@DOT@@"
    processed = stripped

    for pattern in _ABBREVIATION_PATTERNS:

        def _mask_dot(match: re.Match[str]) -> str:
            return match.group(0).replace(".", placeholder)

        processed = re.sub(pattern, _mask_dot, processed, flags=re.IGNORECASE)

    raw_segments = re.split(r"(?<=[.!?])\s+|\r?\n+", processed)

    sentences: list[str] = []
    for segment in raw_segments:
        restored = segment.replace(placeholder, ".").strip()
        if restored:
            sentences.append(restored)

    return sentences

def tokenize(text: str) -> list[str]:
    if not text or not isinstance(text, str):
        return []

    return re.findall(r"\b\w+\b", text)

def remove_stopwords(
    tokens: list[str], extra_stopwords: list[str] | None = None
) -> list[str]:
    if not tokens:
        return []

    stopwords = set(ENGLISH_STOPWORDS)
    if extra_stopwords:
        stopwords.update(word.lower() for word in extra_stopwords if word)

    return [token for token in tokens if token.lower() not in stopwords]

def preprocess_for_tfidf(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    normalized = normalize_text(text)
    cleaned = clean_text(normalized)
    tokens = tokenize(cleaned)
    filtered = remove_stopwords(tokens)

    return " ".join(t.lower() for t in filtered)

def preprocess_for_embedding(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    normalized = normalize_text(text)
    return clean_text(normalized)

def normalize_skill_name(skill: str) -> str:
    if not skill or not isinstance(skill, str):
        return ""

    return re.sub(r"\s+", " ", skill.strip().lower())
