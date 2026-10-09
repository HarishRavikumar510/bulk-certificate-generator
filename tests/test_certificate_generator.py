from datetime import date

from app.services.certificate_generator import generate_certificate


def test_generates_a_valid_pdf(pdf_out_dir):
    path = generate_certificate(
        recipient_name="Test User",
        event_name="Sample Event",
        event_date=date(2025, 1, 15),
    )
    assert path.exists()
    assert path.stat().st_size > 0
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-"  # real PDF magic bytes


def test_very_long_name_does_not_crash(pdf_out_dir):
    path = generate_certificate(
        recipient_name="A" * 300,  # way beyond page width
        event_name="E" * 300,
        event_date=date(2025, 1, 15),
    )
    assert path.exists()  # _fit_font shrank it instead of crashing