"""
Resume Parser Engine
Extracts structured information from resumes using regex + NLP heuristics.
Supports PDF, DOCX, and TXT formats.
"""

import re
import os
import json
from datetime import datetime


# ── optional heavy deps (graceful fallback) ──────────────────────────────────
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    NLP_SUPPORT = True
except Exception:
    NLP_SUPPORT = False


# ── Data ─────────────────────────────────────────────────────────────────────

SKILLS_DB = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "bash",
        "shell", "powershell", "dart", "elixir", "haskell", "lua", "assembly"
    ],
    "web": [
        "html", "css", "react", "angular", "vue", "node.js", "express", "django",
        "flask", "fastapi", "spring", "asp.net", "next.js", "nuxt.js", "svelte",
        "jquery", "bootstrap", "tailwind", "webpack", "graphql", "rest api", "soap"
    ],
    "data": [
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "oracle", "sqlite", "firebase",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "tableau", "power bi", "excel", "spark", "hadoop", "hive", "kafka"
    ],
    "ml_ai": [
        "machine learning", "deep learning", "neural networks", "nlp",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "xgboost", "lightgbm", "hugging face", "transformers", "llm", "bert",
        "gpt", "reinforcement learning", "opencv", "yolo"
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "git", "github", "gitlab", "ci/cd", "linux", "nginx",
        "apache", "microservices", "serverless", "lambda", "ec2", "s3"
    ],
    "soft": [
        "leadership", "communication", "teamwork", "problem solving", "agile",
        "scrum", "project management", "critical thinking", "collaboration",
        "time management", "presentation", "mentoring"
    ]
}

ALL_SKILLS = [s for skills in SKILLS_DB.values() for s in skills]

SECTION_HEADERS = {
    "education":    r"(education|academic|qualification|degree|university|college)",
    "experience":   r"(experience|work history|employment|career|professional background|internship)",
    "skills":       r"(skills|technical skills|competencies|technologies|tools|expertise|proficiencies)",
    "projects":     r"(projects|portfolio|works|assignments|case studies)",
    "certifications": r"(certif|licenses|credentials|accreditation)",
    "summary":      r"(summary|objective|profile|about|overview|introduction)",
    "achievements": r"(achievements|awards|honors|accomplishments|recognition)",
    "languages":    r"(languages|language proficiency)",
    "publications": r"(publications|papers|research|articles)",
    "references":   r"(references|referees)",
}

DEGREE_PATTERNS = [
    r"b\.?tech|bachelor of technology",
    r"b\.?e\.?|bachelor of engineering",
    r"b\.?sc\.?|bachelor of science",
    r"b\.?a\.?|bachelor of arts",
    r"b\.?com|bachelor of commerce",
    r"m\.?tech|master of technology",
    r"m\.?sc\.?|master of science",
    r"m\.?b\.?a|master of business",
    r"m\.?c\.?a|master of computer",
    r"ph\.?d|doctor of philosophy",
    r"diploma|associate",
]

DATE_PATTERN = re.compile(
    r"""
    (?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
       jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)
    \.?\s*\d{4}
    |
    \d{1,2}[\/\-]\d{4}
    |
    \d{4}\s*[-–]\s*(?:\d{4}|present|current|now|ongoing)
    |
    \d{4}
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ── Extractor helpers ─────────────────────────────────────────────────────────

def extract_email(text):
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def extract_phone(text):
    patterns = [
        r"(?:\+91[\-\s]?)?[6-9]\d{9}",
        r"(?:\+1[\-\s]?)?\(?\d{3}\)?[\-\s]\d{3}[\-\s]\d{4}",
        r"(?:\+\d{1,3}[\-\s]?)?\d{10,14}",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group().strip()
    return None


def extract_linkedin(text):
    m = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    return "https://" + m.group() if m else None


def extract_github(text):
    m = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
    return "https://" + m.group() if m else None


def extract_name(text):
    """Heuristic: first non-empty, non-contact line, title-cased."""
    if NLP_SUPPORT:
        doc = nlp(text[:500])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    ignore = re.compile(
        r"resume|curriculum|vitae|cv|email|phone|linkedin|github|@|http|www|\d{10}",
        re.IGNORECASE,
    )
    for line in lines[:6]:
        words = line.split()
        if 1 < len(words) <= 5 and not ignore.search(line):
            if all(w[0].isupper() for w in words if w):
                return line
    return None


def extract_skills(text):
    text_lower = text.lower()
    found = {cat: [] for cat in SKILLS_DB}
    for cat, skills in SKILLS_DB.items():
        for skill in skills:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found[cat].append(skill.title() if len(skill) <= 3 else skill.capitalize())
    return {k: v for k, v in found.items() if v}


def extract_sections(text):
    """Split resume text into labelled sections."""
    lines = text.split("\n")
    sections = {}
    current = "header"
    buffer = []

    for line in lines:
        stripped = line.strip()
        matched_section = None
        for sec, pattern in SECTION_HEADERS.items():
            if re.match(r"^" + pattern + r"[\s:]*$", stripped, re.IGNORECASE):
                matched_section = sec
                break

        if matched_section:
            sections[current] = "\n".join(buffer).strip()
            current = matched_section
            buffer = []
        else:
            buffer.append(line)

    sections[current] = "\n".join(buffer).strip()
    return sections


def extract_education(text):
    results = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        for deg in DEGREE_PATTERNS:
            if re.search(deg, line, re.IGNORECASE):
                context = " ".join(lines[max(0, i-1):i+3])
                dates = DATE_PATTERN.findall(context)
                results.append({
                    "degree": line,
                    "institution": lines[i+1] if i+1 < len(lines) else "",
                    "dates": dates,
                })
                break
    return results


def extract_experience(text):
    results = []
    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        if not block.strip():
            continue
        dates = DATE_PATTERN.findall(block)
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if dates and lines:
            results.append({
                "title": lines[0],
                "company": lines[1] if len(lines) > 1 else "",
                "dates": dates,
                "description": "\n".join(lines[2:]) if len(lines) > 2 else "",
            })
    return results


def extract_projects(text):
    results = []
    blocks = re.split(r"\n{2,}", text)
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if lines:
            desc = "\n".join(lines[1:])
            techs = []
            for skill in ALL_SKILLS:
                if re.search(r"\b" + re.escape(skill) + r"\b", desc, re.IGNORECASE):
                    techs.append(skill.capitalize())
            results.append({
                "name": lines[0],
                "description": desc[:300],
                "technologies": techs[:8],
            })
    return results[:5]


def calculate_score(parsed):
    score = 0
    max_score = 100
    weights = {
        "contact": 20,
        "summary": 10,
        "skills": 25,
        "experience": 25,
        "education": 15,
        "projects": 5,
    }

    contact = parsed.get("contact", {})
    if contact.get("email"):    score += weights["contact"] * 0.4
    if contact.get("phone"):    score += weights["contact"] * 0.3
    if contact.get("linkedin"): score += weights["contact"] * 0.3

    if parsed.get("summary"):   score += weights["summary"]

    skills_flat = sum(len(v) for v in parsed.get("skills", {}).values())
    score += min(weights["skills"], skills_flat * 2)

    exp = parsed.get("experience", [])
    score += min(weights["experience"], len(exp) * 8)

    edu = parsed.get("education", [])
    score += min(weights["education"], len(edu) * 7)

    proj = parsed.get("projects", [])
    score += min(weights["projects"], len(proj) * 2)

    return round(min(score, max_score))


# ── Main Parser class ─────────────────────────────────────────────────────────

class ResumeParser:

    def parse(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            text = self._read_pdf(filepath)
        elif ext == ".docx":
            text = self._read_docx(filepath)
        else:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        return self.parse_text(text)

    def parse_text(self, text):
        sections = extract_sections(text)
        header_text = sections.get("header", text[:1000])

        skills_text = sections.get("skills", "") + "\n" + text
        exp_text    = sections.get("experience", "")
        edu_text    = sections.get("education", "")
        proj_text   = sections.get("projects", "")

        parsed = {
            "meta": {
                "parsed_at": datetime.now().isoformat(),
                "word_count": len(text.split()),
            },
            "contact": {
                "name":     extract_name(text),
                "email":    extract_email(text),
                "phone":    extract_phone(text),
                "linkedin": extract_linkedin(text),
                "github":   extract_github(text),
            },
            "summary":        sections.get("summary", ""),
            "skills":         extract_skills(skills_text),
            "experience":     extract_experience(exp_text) if exp_text else [],
            "education":      extract_education(edu_text) if edu_text else extract_education(text),
            "projects":       extract_projects(proj_text) if proj_text else [],
            "certifications": sections.get("certifications", ""),
            "languages":      sections.get("languages", ""),
            "achievements":   sections.get("achievements", ""),
            "raw_sections":   {k: v[:500] for k, v in sections.items()},
        }

        parsed["score"] = calculate_score(parsed)
        parsed["skill_count"] = sum(len(v) for v in parsed["skills"].values())
        return parsed

    def _read_pdf(self, path):
        if not PDF_SUPPORT:
            raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text

    def _read_docx(self, path):
        if not DOCX_SUPPORT:
            raise ImportError("python-docx not installed. Run: pip install python-docx")
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
