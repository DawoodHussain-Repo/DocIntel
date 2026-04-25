"""PDF report generation for analyzed contracts."""

from __future__ import annotations

from io import BytesIO
from typing import Tuple

from core.errors import AppError
from core.models import DocumentAnalysisData


def _risk_color(level: str) -> Tuple[float, float, float]:
    if level == "green":
        return (0.13, 0.77, 0.37)
    if level == "yellow":
        return (0.92, 0.70, 0.03)
    return (0.94, 0.27, 0.27)


def render_analysis_report_pdf(analysis: DocumentAnalysisData) -> bytes:
    """
    Render a simple PDF report for download.

    Dependency: reportlab (optional).
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except Exception as error:
        raise AppError(
            message="PDF report generation requires the 'reportlab' package.",
            code="REPORT_DEP_MISSING",
            status_code=422,
            details={"hint": "pip install reportlab", "error": str(error)},
        ) from error

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    x = 0.9 * inch
    y = height - 0.9 * inch

    c.setTitle(f"DocIntel Report - {analysis.file}")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "DocIntel Contract Report")
    y -= 0.25 * inch

    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"File: {analysis.file}")
    y -= 0.18 * inch
    c.drawString(
        x,
        y,
        f"Type: {analysis.classification.contract_type} (confidence {analysis.classification.confidence:.2f})",
    )
    y -= 0.25 * inch

    # Risk badge
    r, g, b = _risk_color(analysis.risk.level)
    c.setFillColorRGB(r, g, b)
    c.circle(x + 12, y + 4, 6, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 26, y, f"Risk score: {analysis.risk.overall_score}/100 ({analysis.risk.level})")
    c.setFillColorRGB(1, 1, 1)
    y -= 0.35 * inch

    # Executive summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Executive Summary")
    y -= 0.2 * inch
    c.setFont("Helvetica", 10)
    for bullet in analysis.executive_summary:
        wrapped = _wrap_text(bullet, max_chars=95)
        for idx, line in enumerate(wrapped):
            prefix = "• " if idx == 0 else "  "
            c.drawString(x, y, prefix + line)
            y -= 0.16 * inch
        y -= 0.04 * inch

    y -= 0.12 * inch

    # Red flags
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Red Flags")
    y -= 0.2 * inch
    c.setFont("Helvetica", 10)
    flags = analysis.risk.red_flags[:6]
    if not flags:
        c.drawString(x, y, "None detected from the analyzed excerpts.")
        y -= 0.18 * inch
    else:
        for flag in flags:
            title_line = f"{flag.title} ({flag.severity})"
            for idx, line in enumerate(_wrap_text(title_line, max_chars=95)):
                prefix = "• " if idx == 0 else "  "
                c.drawString(x, y, prefix + line)
                y -= 0.16 * inch
            for line in _wrap_text(flag.description, max_chars=95)[:3]:
                c.drawString(x + 16, y, line)
                y -= 0.16 * inch
            y -= 0.06 * inch

    c.showPage()
    c.save()
    return buffer.getvalue()


def _wrap_text(text: str, max_chars: int = 90) -> list[str]:
    words = (text or "").split()
    lines: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        candidate = length + len(word) + (1 if current else 0)
        if candidate > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length = candidate
    if current:
        lines.append(" ".join(current))
    return lines or [""]

