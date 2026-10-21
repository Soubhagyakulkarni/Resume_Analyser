"""Deterministic helpers for building resume sections from user-provided content."""

import re
from dataclasses import dataclass

_MEASURABLE_OUTCOME = re.compile(
    r"\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\s+"
    r"(?:users?|customers?|students?|people|hours?|days?|weeks?|projects?|"
    r"records?|requests?|tickets?|participants?|attendees?|tasks?|minutes?)\b"
    r"|[$]\s*\d+(?:[.,]\d+)*",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ResumeDraft:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    target_role: str = ""
    linkedin: str = ""
    portfolio: str = ""
    summary: str = ""
    education: str = ""
    skills: str = ""
    experience: str = ""
    projects: str = ""
    certifications: str = ""


def build_resume_sections(draft: ResumeDraft) -> list[tuple[str, str]]:
    """Return non-empty, ordered sections without inventing missing information."""
    candidates = (
        ("Profile", draft.summary),
        ("Education", draft.education),
        ("Experience", draft.experience),
        ("Projects", draft.projects),
        ("Skills", draft.skills),
        ("Certifications", draft.certifications),
    )
    return [(heading, content.strip()) for heading, content in candidates if content.strip()]


def build_contact_line(draft: ResumeDraft) -> str:
    """Join the optional contact fields in a compact, readable line."""
    return "  |  ".join(
        value.strip()
        for value in (
            draft.email,
            draft.phone,
            draft.location,
            draft.linkedin,
            draft.portfolio,
        )
        if value.strip()
    )


# Common resume section headings
_SECTION_RE = re.compile(
    r"^(?:professional\s+)?"
    r"(?:summary|profile|objective|about(?:\s+me)?|"
    r"education(?:al)?(?:\s+details)?|academic|qualifications?|"
    r"skills|technical\s+skills|core\s+competencies|"
    r"experience|work\s+experience|employment(?:\s+history)?|internships?|"
    r"projects?|certification|certifications|awards?|"
    r"achievements?|activities|extra[\s-]*curricular|interests|hobbies|languages|"
    r"publications?|references?|volunteer(?:ing)?|"
    r"leadership(?:\s*[&]\s*achievements?)?|links?|"
    r"contact(?:\s+info(?:rmation)?)?)"
    r"s?\s*:?\s*$",
    re.IGNORECASE,
)


def clean_resume_text(text: str) -> str:
    """Normalize extracted text symbols, bullets, and dashes."""
    # Normalize unicode dashes and quotes to clean standard characters
    cleaned = (
        text.replace("\u2013", " - ")
        .replace("\u2014", " - ")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    # Replace \ufffd or stray markers at line start with bullet
    cleaned = re.sub(r"(?m)^[ \t]*[\ufffd•▪■*\-–◦·]\s*", "• ", cleaned)
    # Replace \ufffd between numbers or years with dash
    cleaned = re.sub(r"(\d)\s*[\ufffd–-]\s*(\d)", r"\1 - \2", cleaned)
    # Replace \ufffd between words with pipe
    cleaned = re.sub(r"([A-Za-z0-9])\s*[\ufffd]\s*([A-Za-z0-9])", r"\1 | \2", cleaned)
    return cleaned.replace("\ufffd", " ")


def split_existing_resume(text: str) -> list[tuple[str, str]]:
    """Split extracted/pasted resume text into sections by detecting headings."""
    cleaned = clean_resume_text(text.strip())
    if not cleaned:
        return []

    lines = cleaned.split("\n")
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if _SECTION_RE.match(stripped):
            # Save previous section if we had one
            if current_heading and current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_heading, body))
            current_heading = stripped.rstrip(":").strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_heading and current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_heading, body))

    # shortcut: if no headings detected, fall back to single section
    if not sections and cleaned:
        sections = [("Resume content", cleaned)]

    return sections


def extract_name_from_text(text: str) -> str:
    """Best-effort: first non-empty line that looks like a name (short, no special chars)."""
    cleaned = clean_resume_text(text.strip())
    for line in cleaned.split("\n")[:6]:
        line = line.strip()
        if not line or _SECTION_RE.match(line):
            continue
        if line.lower() in ("resume", "curriculum vitae", "cv", "resume content", "header"):
            continue
        if "@" in line or line.startswith(("http", "www.", "+", "(")) or len(line) > 60:
            continue
        clean_chars = line.replace(" ", "").replace(".", "").replace("-", "")
        if len(line.split()) <= 5 and (clean_chars.isalpha() or not clean_chars):
            return line
    return "Resume"


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?<![\w/.-])(\+?\d[\d\s\-().]{7,}\d)(?![\w/.-])")
_URL_RE = re.compile(
    r"(?:https?://[^\s|]+|(?:www\.|linkedin\.com/in/|github\.com/|codolio\.com/)[^\s|]*)",
    re.IGNORECASE,
)


def extract_contact_from_text(text: str) -> str:
    """Pull contact info (email, phone, URLs, location) from lines before the first heading."""
    parts: list[str] = []
    lines = clean_resume_text(text.strip()).split("\n")[:10]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _SECTION_RE.match(stripped):
            break  # stop at first section heading
        # Collect URLs and emails first
        urls = _URL_RE.findall(stripped)
        emails = _EMAIL_RE.findall(stripped)
        # Strip URLs before phone extraction to prevent matching digits inside URL slugs
        no_urls = _URL_RE.sub("", stripped)
        phones = _PHONE_RE.findall(no_urls)

        for phone in phones:
            phone_clean = phone.strip()
            if len(phone_clean) >= 8:
                parts.append(phone_clean)
        parts.extend(emails)
        parts.extend(urls)

        # Check for location-like segment (City, State / Region)
        for segment in re.split(r"[|•·]", stripped):
            seg = segment.strip()
            if (
                seg
                and not _EMAIL_RE.search(seg)
                and not _PHONE_RE.search(seg)
                and not _URL_RE.search(seg)
            ):
                if "," in seg and len(seg) < 50:
                    parts.append(seg)

    return "  |  ".join(dict.fromkeys(parts))  # deduplicate preserving order



def review_resume_draft(draft: ResumeDraft) -> tuple[int, list[tuple[str, str, str]]]:
    """Return a transparent completeness indicator and deterministic editing suggestions."""
    sections = build_resume_sections(draft)
    content = " ".join(section_content for _, section_content in sections)
    checks = [
        (
            "Contact details",
            "Complete" if draft.full_name.strip() and draft.email.strip() else "Add detail",
            "Add your name and a professional email address.",
        ),
        (
            "Profile",
            "Complete" if len(draft.summary.split()) >= 20 else "Add detail",
            "Write a focused 2–4 line profile with your direction and strongest evidence.",
        ),
        (
            "Education",
            "Complete" if bool(draft.education.strip()) else "Add detail",
            "Include your qualification, institution, and expected or completion date.",
        ),
        (
            "Skills",
            "Complete" if bool(draft.skills.strip()) else "Add detail",
            "List relevant skills you can demonstrate through a project or experience.",
        ),
        (
            "Practical evidence",
            "Complete"
            if bool(draft.experience.strip() or draft.projects.strip())
            else "Add detail",
            "Add at least one project, internship, job, volunteering, or leadership example.",
        ),
        (
            "Impact",
            "Complete" if _MEASURABLE_OUTCOME.search(content) else "Consider",
            "Where accurate, add a measurable result such as users reached, time saved, or scope.",
        ),
    ]
    completed = sum(status == "Complete" for _, status, _ in checks)
    completeness = round(completed / len(checks) * 100)
    return completeness, checks
