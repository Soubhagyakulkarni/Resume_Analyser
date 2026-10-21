"""Render user-authored resume content as a clean, professional PDF."""

import re
from io import BytesIO
from typing import ClassVar
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Matches URLs and domain links
_URL_RE = re.compile(
    r"(https?://[^\s<>\"'\)]+|(?:www\.|linkedin\.com/|github\.com/|codolio\.com/)[^\s<>\"'\)]+)",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")

# Known skill categories that may appear adjacent to skills in extracted text
_KNOWN_SKILL_CATS = (
    "programming languages",
    "programming language",
    "tools and technologies",
    "tools & technologies",
    "core computer science",
    "frontend",
    "backend",
    "databases",
    "database",
    "frameworks & tools",
    "frameworks and tools",
    "frameworks",
    "libraries",
    "web technologies",
    "cloud & devops",
    "cloud",
    "devops",
    "languages",
    "technical skills",
    "operating systems",
    "certifications",
    "soft skills",
)

# Date pattern for right-aligned entry headers (e.g. 2024 - 2028, 2026, Present)
_DATE_SUFFIX_RE = re.compile(
    r"^(.*?)\s*(\b(?:19|20)\d{2}\s*[\-–—to\s]+\s*(?:(?:19|20)\d{2}|Present|Current|Ongoing)|\b(?:19|20)\d{2})\s*$",
    re.IGNORECASE,
)


def _linkify(text: str) -> str:
    """Escape text for ReportLab XML, then wrap URLs and emails in active <a> tags."""
    safe = escape(text)

    def _url_sub(m: re.Match) -> str:
        url = m.group(0).rstrip(".,;")
        href = url if url.startswith(("http://", "https://")) else f"https://{url}"
        return f'<a href="{href}" color="#0B57D0"><u>{url}</u></a>'

    def _email_sub(m: re.Match) -> str:
        email = m.group(0)
        return f'<a href="mailto:{email}" color="#0B57D0"><u>{email}</u></a>'

    safe = _URL_RE.sub(_url_sub, safe)
    safe = _EMAIL_RE.sub(_email_sub, safe)
    return safe


def _format_skill_line(line: str) -> str:
    """Detect and format skill categories cleanly as bold prefixes."""
    stripped = line.strip()
    lower = stripped.lower()
    for cat in _KNOWN_SKILL_CATS:
        if lower.startswith(cat):
            rest = stripped[len(cat):].lstrip(": –-|")
            cat_display = stripped[:len(cat)]
            if rest:
                return f"<b>{escape(cat_display)}:</b> {_linkify(rest.strip())}"
            return f"<b>{escape(cat_display)}</b>"

    # Pattern: "Category: Skills" or "Category - Skills"
    m = re.match(r"^([^:–|]{2,35})[:–|]\s*(.+)$", stripped)
    if m:
        return f"<b>{escape(m.group(1).strip())}:</b> {_linkify(m.group(2).strip())}"

    return _linkify(stripped)


class ResumePdfRenderer:
    """Create a printable, professional resume PDF."""

    _TEMPLATES: ClassVar[dict[str, tuple[str, int, float]]] = {
        # accent_color, name_font_size, margin_inches
        "Classic": ("#111827", 18, 0.55),
        "Modern": ("#1E3A8A", 20, 0.55),
        "Compact": ("#111827", 16, 0.45),
    }

    def render(
        self,
        name: str,
        contact_line: str,
        sections: list[tuple[str, str]],
        template: str = "Classic",
        subtitle: str = "",
    ) -> bytes:
        accent, name_size, margin = self._TEMPLATES.get(
            template, self._TEMPLATES["Classic"]
        )
        compact = template == "Compact"
        body_size = 9 if compact else 9.5
        body_leading = body_size + 3

        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=letter,
            rightMargin=margin * inch,
            leftMargin=margin * inch,
            topMargin=(0.4 if compact else 0.5) * inch,
            bottomMargin=(0.4 if compact else 0.5) * inch,
            title=name.strip() or "Resume",
            author="",
        )
        styles = getSampleStyleSheet()
        accent_color = colors.HexColor(accent)
        text_color = colors.HexColor("#1A1A1A")
        muted_color = colors.HexColor("#4B5563")
        line_color = colors.HexColor("#374151")

        avail_width = (8.5 - 2 * margin) * inch

        # Typography matching industry standard resumes (Jake's Resume / Overleaf LaTeX style)
        name_style = ParagraphStyle(
            "ResumeName",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=name_size,
            leading=name_size + 4,
            textColor=text_color,
            alignment=TA_CENTER,
            spaceAfter=2,
            spaceBefore=0,
        )
        contact_style = ParagraphStyle(
            "ResumeContact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5 if compact else 9,
            leading=12,
            textColor=muted_color,
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "ResumeSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=accent_color,
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        section_heading_style = ParagraphStyle(
            "ResumeSectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5 if compact else 11,
            leading=14,
            textColor=accent_color,
            spaceBefore=6 if compact else 8,
            spaceAfter=1,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "ResumeBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=body_size,
            leading=body_leading,
            textColor=text_color,
            alignment=TA_JUSTIFY,
            spaceAfter=1.5,
        )
        bullet_style = ParagraphStyle(
            "ResumeBullet",
            parent=body_style,
            bulletIndent=4,
            leftIndent=16,
            spaceBefore=0,
            spaceAfter=1,
            alignment=TA_LEFT,
        )
        entry_left_style = ParagraphStyle(
            "ResumeEntryLeft",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=body_size,
            leading=body_leading,
            textColor=text_color,
            alignment=TA_LEFT,
        )
        entry_right_style = ParagraphStyle(
            "ResumeEntryRight",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=body_size,
            leading=body_leading,
            textColor=muted_color,
            alignment=TA_RIGHT,
        )

        story: list = []

        # Header: Name
        display_name = name.strip() or "Resume"
        story.append(Paragraph(escape(display_name), name_style))

        # Target Role / Subtitle
        if subtitle.strip():
            story.append(Paragraph(escape(subtitle.strip()), subtitle_style))

        # Contact line
        if contact_line.strip():
            story.append(Paragraph(_linkify(contact_line.strip()), contact_style))

        # Header horizontal divider
        story.append(Spacer(1, 2))
        story.append(HRFlowable(
            width="100%",
            thickness=1.2,
            color=accent_color,
            spaceBefore=1,
            spaceAfter=3,
        ))

        # Sections
        for heading, content in sections:
            clean_heading = heading.strip()
            if not clean_heading:
                continue

            # Heading with underline
            story.append(Paragraph(escape(clean_heading), section_heading_style))
            story.append(HRFlowable(
                width="100%",
                thickness=0.5,
                color=line_color,
                spaceBefore=1,
                spaceAfter=3,
            ))

            raw_body = content.strip()
            if not raw_body:
                story.append(Paragraph("Not provided.", body_style))
                continue

            is_skills = "skill" in clean_heading.lower()

            for line in raw_body.split("\n"):
                stripped = line.strip()
                if not stripped:
                    story.append(Spacer(1, 2))
                    continue

                # Skills section
                if is_skills:
                    story.append(Paragraph(_format_skill_line(stripped), body_style))
                    continue

                # Bullet items
                if stripped.startswith(("•", "-", "–", "▪", "■", "*", "·", "◦", "\ufffd")):
                    bullet_body = stripped.lstrip("•-–▪■*·◦\ufffd ")
                    story.append(Paragraph(_linkify(bullet_body), bullet_style, bulletText="•"))
                    continue

                # Pipe-delimited entry headers (e.g. "Role | Org | Dates" or "Title | Dates")
                if "|" in stripped:
                    parts = [p.strip() for p in stripped.split("|") if p.strip()]
                    if len(parts) >= 2:
                        left_content = f"<b>{_linkify(parts[0])}</b>"
                        if len(parts) >= 3:
                            left_content += f"  |  <i>{_linkify(parts[1])}</i>"
                        right_content = f"<i>{_linkify(parts[-1])}</i>"
                        entry_table = Table(
                            [[
                                Paragraph(left_content, entry_left_style),
                                Paragraph(right_content, entry_right_style),
                            ]],
                            colWidths=[avail_width * 0.72, avail_width * 0.28],
                        )
                        entry_table.setStyle(TableStyle([
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 1),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                        ]))
                        story.append(entry_table)
                        continue

                # Check for entry title with dates at the end (e.g. "Degree Name 2024 - 2028")
                date_match = _DATE_SUFFIX_RE.match(stripped)
                if date_match and len(date_match.group(1).strip()) > 3:
                    left_text = date_match.group(1).strip()
                    right_text = date_match.group(2).strip()
                    entry_table = Table(
                        [[
                            Paragraph(f"<b>{_linkify(left_text)}</b>", entry_left_style),
                            Paragraph(f"<i>{_linkify(right_text)}</i>", entry_right_style),
                        ]],
                        colWidths=[avail_width * 0.72, avail_width * 0.28],
                    )
                    entry_table.setStyle(TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ]))
                    story.append(entry_table)
                    continue

                # Regular body line
                story.append(Paragraph(_linkify(stripped), body_style))

        document.build(story)
        return output.getvalue()
