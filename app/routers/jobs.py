"""HTTP layer: request handling only. All logic lives in services."""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Certificate, CertificateJob, CertificateStatus
from ..schemas import CertificateJobCreate, CertificateOut, JobOut
from ..services.job_processor import process_job

router = APIRouter()


# ---------- response builders ----------

def _certificate_to_out(job_id: str, cert: Certificate) -> CertificateOut:
    download_url = None
    if cert.status == CertificateStatus.COMPLETED and cert.file_path:
        download_url = f"/api/certificate-jobs/{job_id}/certificates/{cert.id}/download"
    return CertificateOut(
        id=cert.id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status,
        error_message=cert.error_message,
        download_url=download_url,
    )


def _job_to_out(job: CertificateJob) -> JobOut:
    certs = [_certificate_to_out(job.id, c) for c in job.certificates]
    return JobOut(
        id=job.id,
        event_name=job.event_name,
        event_date=job.event_date,
        status=job.status,
        total_recipients=len(certs),
        completed_count=sum(1 for c in certs if c.status == CertificateStatus.COMPLETED),
        failed_count=sum(1 for c in certs if c.status == CertificateStatus.FAILED),
        pending_count=sum(1 for c in certs if c.status == CertificateStatus.PENDING),
        created_at=job.created_at.isoformat(),
        certificates=certs,
    )


# ---------- endpoints ----------

@router.post("", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_certificate_job(
    payload: CertificateJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    event_name = payload.event_name.strip()
    if not event_name:
        raise HTTPException(status_code=422, detail="event_name cannot be blank")

    job = CertificateJob(event_name=event_name, event_date=payload.event_date)
    for recipient in payload.recipients:
        job.certificates.append(
            Certificate(
                recipient_name=(recipient.name or "").strip(),
                recipient_email=(recipient.email or "").strip(),
            )
        )
    db.add(job)
    db.commit()  # expire_on_commit=False → attributes stay usable below

    # Fire-and-forget: runs AFTER the response is delivered
    background_tasks.add_task(process_job, job.id)

    return _job_to_out(job)


@router.get("/{job_id}", response_model=JobOut)
def get_certificate_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(CertificateJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_out(job)


@router.get("/{job_id}/certificates/{certificate_id}/download")
def download_certificate(job_id: str, certificate_id: str, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if cert is None or cert.job_id != job_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != CertificateStatus.COMPLETED or not cert.file_path:
        raise HTTPException(status_code=400, detail="Certificate not available for download")
    file = Path(cert.file_path)
    if not file.is_file():
        raise HTTPException(status_code=404, detail="Certificate file missing on disk")

    return FileResponse(
        path=file,
        media_type="application/pdf",
        filename=f"certificate-{cert.id}.pdf",
    )