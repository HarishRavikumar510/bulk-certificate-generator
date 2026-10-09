"""PDF certificate rendering with ReportLab.

Pure business logic: takes certificate data in, produces a PDF file on
disk and returns its path. Knows nothing about HTTP or the database.
"""

import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from ..config import settings

# --- Page & palette constants -------------------------------------------

PAGE_W, PAGE_H = landscape(A4)

ACCENT = HexColor("#1a5276")   # deep blue
BAND = HexColor("#eaf2f8")     # light blue
TEXT = HexColor("#212f3d")     # near-black
MUTED = HexColor("#7f8c8d")    # grey


def _fit_font(text: str, font: str, max_size: int, min_size: int, max_width: float) -> int:
    """Shrink font size until the text fits max_width (handles long names)."""
    size = max_size
    while size > min_size and stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def generate_certificate(
    *,
    recipient_name: str,
    event_name: str,
    event_date: date,
    certificate_id: str | None = None,
) -> Path:
    """Render one certificate PDF and return the file path."""
    certificate_id = certificate_id or uuid.uuid4().hex
    file_path = settings.CERTIFICATE_OUTPUT_DIR / f"{certificate_id}.pdf"

    canvas = Canvas(str(file_path), pagesize=(PAGE_W, PAGE_H))

    # Double border
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(6)
    canvas.rect(30, 30, PAGE_W - 60, PAGE_H - 60)
    canvas.setLineWidth(1.5)
    canvas.rect(42, 42, PAGE_W - 84, PAGE_H - 84)

    # Header band
    canvas.setFillColor(BAND)
    canvas.rect(42, PAGE_H - 150, PAGE_W - 84, 100, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica-Bold", 34)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 100, "CERTIFICATE")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 13)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 128, "OF COMPLETION")

    # "presented to"
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 14)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 200, "This certificate is proudly presented to")

    # Recipient name (auto-shrinks if long)
    name_size = _fit_font(recipient_name, "Times-Bold", 44, 20, PAGE_W - 200)
    canvas.setFillColor(TEXT)
    canvas.setFont("Times-Bold", name_size)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 270, recipient_name)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(PAGE_W / 2 - 220, PAGE_H - 286, PAGE_W / 2 + 220, PAGE_H - 286)

    # Event info
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 14)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 330, "for successfully completing")
    canvas.setFillColor(ACCENT)
    event_size = _fit_font(event_name, "Helvetica-Bold", 26, 14, PAGE_W - 200)
    canvas.setFont("Helvetica-Bold", event_size)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 370, event_name)
    canvas.setFillColor(TEXT)
    canvas.setFont("Helvetica", 14)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 405, f"Held on {event_date.strftime('%d %B %Y')}")

    # Seal
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(2)
    canvas.circle(PAGE_W - 115, 115, 42)
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(PAGE_W - 115, 120, "VERIFIED")
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(PAGE_W - 115, 104, "CERTIFICATE")

    # Footer: unique ID + issue timestamp
    issued = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(PAGE_W / 2, 52, f"Certificate ID: {certificate_id}  •  Issued: {issued}")

    canvas.save()
    return file_path


# --- Quick manual test:  python -m app.services.certificate_generator ----

if __name__ == "__main__":
    path = generate_certificate(
        recipient_name="Harish Ravikumar",
        event_name="AWS Cloud Practitioner Workshop",
        event_date=date(2025, 1, 15),
    )
    print(f"Generated: {path}")