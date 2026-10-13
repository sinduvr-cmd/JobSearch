"""Normalization service for text sanitization, token-aware skill extraction,
alias resolution, work-model classification, and deterministic matching.
"""

import re
import html
import bleach
from typing import List, Dict, Any, Optional, Set, Tuple

# Predefined canonical skill aliases map (lowercase alias -> canonical display name)
SKILL_ALIASES: Dict[str, str] = {
    # Data & AI/ML
    "python": "Python",
    "py": "Python",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "AI",
    "artificial intelligence": "AI",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "data science": "Data Science",
    "data scientist": "Data Science",
    "data analysis": "Data Analysis",
    "data analyst": "Data Analysis",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "bigquery": "BigQuery",
    "snowflake": "Snowflake",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",
    "spark": "Spark",
    "pyspark": "PySpark",
    "kafka": "Kafka",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "llm": "LLMs",
    "llms": "LLMs",
    "langchain": "LangChain",
    "mlops": "MLOps",
    
    # Software Engineering & Backend
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "rails": "Ruby on Rails",
    "php": "PHP",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "swift": "Swift",
    ".net": ".NET",
    "dotnet": ".NET",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "backend": "Backend",
    "frontend": "Frontend",
    "fullstack": "Full Stack",
    "full stack": "Full Stack",
    "rest api": "REST API",
    "rest": "REST API",
    "graphql": "GraphQL",
    "microservices": "Microservices",

    # Cloud & DevOps
    "cloud": "Cloud",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "devops": "DevOps",
    "git": "Git",
    "github": "GitHub",
    "linux": "Linux",
}

# Compile token-boundary regular expressions for each alias to avoid substring accidents
# E.g., 'java' shouldn't match 'javascript', 'c' shouldn't match 'cloud' or 'css'
def _compile_skill_pattern(alias: str) -> re.Pattern:
    # Use negative lookbehind and lookahead to ensure token boundary
    # This prevents 'java' from matching 'javascript' and handles '.net', 'c++', 'c#' cleanly
    escaped = re.escape(alias)
    return re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)

COMPILED_SKILL_PATTERNS = [
    (alias, canon, _compile_skill_pattern(alias))
    for alias, canon in SKILL_ALIASES.items()
]


def sanitize_html_text(raw_html: Optional[str]) -> str:
    """Sanitize and strip dangerous HTML tags and script contents from raw job descriptions,
    returning clean readable text while unescaping entities.
    """
    if not raw_html:
        return ""
    # Strip script and style elements along with their contents
    cleaned_input = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    # Strip dangerous tags using bleach
    clean = bleach.clean(
        cleaned_input,
        tags=["p", "br", "ul", "ol", "li", "strong", "b", "em", "i", "h1", "h2", "h3", "h4", "h5", "h6"],
        strip=True
    )
    # Strip HTML tags completely for plain text snippets
    plain = re.sub(r"<[^>]+>", " ", clean)
    plain = html.unescape(plain)
    # Collapse multiple whitespaces and linebreaks
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain


def extract_skills_from_text(text_to_search: str, existing_tags: Optional[List[str]] = None) -> List[str]:
    """Token-aware skill extraction from job title, description, and tags.
    Normalizes aliases to canonical names and eliminates duplicate skills.
    """
    found_skills: Set[str] = set()

    # 1. Process explicit tags provided by the API
    if existing_tags:
        for tag in existing_tags:
            tag_clean = tag.strip().lower()
            if tag_clean in SKILL_ALIASES:
                found_skills.add(SKILL_ALIASES[tag_clean])
            elif tag_clean:
                # Add capitalised representation if not empty
                found_skills.add(tag.strip().title())

    # 2. Token-aware regex search in provided text (title + description snippet)
    if text_to_search:
        # Search lower-cased plain text
        for alias, canon, pattern in COMPILED_SKILL_PATTERNS:
            if canon not in found_skills and pattern.search(text_to_search):
                found_skills.add(canon)

    return sorted(list(found_skills))


def normalize_skill_query(query_str: str) -> List[str]:
    """Parse comma/space-separated user skill query into canonical skill names."""
    if not query_str:
        return []
    parts = re.split(r"[,;/]+", query_str)
    canonical_list = []
    for p in parts:
        p_clean = p.strip()
        if not p_clean:
            continue
        p_lower = p_clean.lower()
        if p_lower in SKILL_ALIASES:
            canonical_list.append(SKILL_ALIASES[p_lower])
        else:
            canonical_list.append(p_clean)
    return list(dict.fromkeys(canonical_list))  # Preserves order, removes duplicates


def determine_work_model(remote: bool, title: str, description: str, location: str) -> str:
    """Classify work model accurately without unwarranted assumptions:
    - If remote is True: check if 'hybrid' is mentioned -> 'Remote / Hybrid', else 'Remote'
    - If remote is False:
        - Check explicit 'hybrid' -> 'Hybrid'
        - Check explicit 'on-site', 'in-office', 'onsite' -> 'On-site'
        - Otherwise mark 'Unknown' (Do not falsely assume on-site just because remote is false)
    """
    combined_text = f"{title} {location} {description}".lower()

    if remote:
        if "hybrid" in combined_text:
            return "Remote / Hybrid"
        return "Remote"

    # Remote flag is False: verify if explicit hybrid or on-site indicators exist
    if "hybrid" in combined_text:
        return "Hybrid"
    if any(k in combined_text for k in ["on-site", "onsite", "in-person", "office-based", "in office"]):
        return "On-site"

    # Default to Unknown for honest reporting
    return "Unknown"


def parse_salary_from_text(text: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str], Optional[str]]:
    """Attempt honest extraction of salary from text without inventing numbers.
    Returns (salary_min, salary_max, currency, period, raw_text).
    """
    if not text:
        return (None, None, None, None, None)

    # Look for patterns like $80,000 - $120,000 or €60.000 - €90.000 or ₹20L - ₹40L
    patterns = [
        # USD / EUR / GBP yearly range e.g. $100k - $140k or $100,000 - $140,000
        r"([$€£₹])\s*(\d{1,3}(?:[,\.]\d{3})*|\d+)\s*(?:k|K)?\s*(?:-|to)\s*([$€£₹])?\s*(\d{1,3}(?:[,\.]\d{3})*|\d+)\s*(k|K)?\s*(?:per\s+(year|month|annum|yr)|/yr|/year|p\.a\.)?",
        # INR Lakhs e.g. ₹20L - ₹35L
        r"(₹|INR|Rs\.?)\s*(\d+(?:\.\d+)?)\s*L\s*(?:-|to)\s*(?:₹|INR)?\s*(\d+(?:\.\d+)?)\s*L",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw_matched = m.group(0).strip()
            # Currency symbol
            curr = m.group(1)
            if curr in ("₹", "INR", "Rs"):
                curr = "INR"
            elif curr == "$":
                curr = "USD"
            elif curr == "€":
                curr = "EUR"
            elif curr == "£":
                curr = "GBP"

            return (None, None, curr, "year", raw_matched)

    return (None, None, None, None, None)
