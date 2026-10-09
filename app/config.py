import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    APP_NAME = "Bulk Certificate Generator"

    # SQLite by default; swap the URL for Postgres without code changes
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")

    # Where generated PDFs are written
    CERTIFICATE_OUTPUT_DIR = Path(
        os.getenv("CERTIFICATE_OUTPUT_DIR", BASE_DIR / "generated_certificates")
    )

    # Threads used for parallel PDF generation (later step)
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))


settings = Settings()
settings.CERTIFICATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)