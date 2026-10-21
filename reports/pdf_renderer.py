"""Accessible, printable in-memory PDF report renderer."""

from datetime import UTC, datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class ReportLabPdfRenderer:
    def render(self, title: str, sections: list[tuple[str, list[str]]]) -> bytes:
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=letter,
            rightMargin=0.7 * inch,
            leftMargin=0.7 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.7 * inch,
            title=title,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CareerReportTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#0c5e59"),
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        date_style = ParagraphStyle(
            "CareerReportDate",
            parent=styles["Normal"],
            textColor=colors.HexColor("#627486"),
            alignment=TA_CENTER,
            fontSize=9,
            spaceAfter=8,
        )
        heading_style = ParagraphStyle(
            "CareerReportHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0c5e59"),
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=7,
            spaceAfter=5,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "CareerReportBody",
            parent=styles["BodyText"],
            textColor=colors.HexColor("#243746"),
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2,
        )
        story = [
            Paragraph(escape(title), title_style),
            Paragraph(f"Generated {datetime.now(UTC).date().isoformat()}", date_style),
            Spacer(1, 12),
        ]
        for heading, lines in sections:
            story.append(Paragraph(escape(heading), heading_style))
            if lines:
                for line in lines:
                    story.append(Paragraph(escape(line), body_style, bulletText="-"))
            else:
                story.append(Paragraph("No items available.", body_style))
            story.append(Spacer(1, 8))

        def add_page_number(canvas, doc) -> None:
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#627486"))
            canvas.drawString(0.7 * inch, 0.4 * inch, "AI Resume Analyzer · Career guidance")
            canvas.drawRightString(letter[0] - 0.7 * inch, 0.4 * inch, f"Page {doc.page}")
            canvas.restoreState()

        document.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        return output.getvalue()
