"""Background processing of certificate jobs.

Runs OUTSIDE the request cycle, so it uses its own DB sessions.

Failure isolation strategy:
- Each certificate is validated and generated inside its own try/except.
- Each certificate row is committed individually, so:
    * one failure never affects other certificates in the job
    * the status endpoint shows LIVE progress while the job runs
    * if the process crashes mid-job, already-completed work is not lost
"""

import re
from datetime import datetime, timezone

from ..database import get_session_factory
from ..models import Certificate, CertificateJob, CertificateStatus, JobStatus
from .certificate_generator import generate_certificate

# Pragmatic email check: something@something.something (no spaces)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validation_error(name: str, email: str) -> str | None:
    """Semantic (per-recipient) validation. Returns a reason, or None if valid."""
    if not name:
        return "Recipient name is missing or empty"
    if len(name) > 200:
        return "Recipient name is too long (max 200 characters)"
    if not email:
        return "Recipient email is missing or empty"
    if not EMAIL_RE.match(email):
        return "Recipient email has an invalid format"
    return None


def process_job(job_id: str) -> None:
    """Generate a certificate for every recipient in the job."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        job = db.get(CertificateJob, job_id)
        if job is None or job.status != JobStatus.PENDING:
            return  # unknown job, or already processed (simple idempotency guard)

        job.status = JobStatus.IN_PROGRESS
        db.commit()

        certificates = (
            db.query(Certificate).filter(Certificate.job_id == job_id).all()
        )

        for cert in certificates:
            try:
                error = _validation_error(cert.recipient_name, cert.recipient_email)
                if error:
                    raise ValueError(error)

                file_path = generate_certificate(
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                    certificate_id=cert.id,  # PDF filename == DB row id
                )
                cert.status = CertificateStatus.COMPLETED
                cert.file_path = str(file_path)
                cert.generated_at = datetime.now(timezone.utc)
                cert.error_message = None
            except Exception as exc:  # noqa: BLE001 -- isolate ANY failure to this row
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(exc)[:500]

            db.commit()  # per-certificate commit → live progress

        job.status = JobStatus.COMPLETED  # completed even with partial failures
        db.commit()
    finally:
        db.close()