from datetime import date
from pydantic import BaseModel, ConfigDict, Field

from .models import CertificateStatus, JobStatus


# ---------- Requests ----------

class RecipientInput(BaseModel):
    """
    Deliberately lenient: name/email are Optional so one bad recipient
    doesn't get the WHOLE request rejected with 422. Semantic validation
    happens per-recipient in the service layer (later step).
    """
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    email: str | None = None


class CertificateJobCreate(BaseModel):
    """Structural validation — if THIS fails, the request is malformed → 422."""
    event_name: str = Field(min_length=1, max_length=200)
    event_date: date
    recipients: list[RecipientInput] = Field(min_length=1, max_length=1000)


# ---------- Responses ----------

class CertificateOut(BaseModel):
    id: str
    recipient_name: str
    recipient_email: str
    status: CertificateStatus
    error_message: str | None = None
    download_url: str | None = None


class JobOut(BaseModel):
    id: str
    event_name: str
    event_date: date
    status: JobStatus
    total_recipients: int
    completed_count: int
    failed_count: int
    pending_count: int
    created_at: str
    certificates: list[CertificateOut]