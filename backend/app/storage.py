from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


DATA_DIR = Path(os.getenv("PDF_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def file_path(file_id: str) -> Path:
    return DATA_DIR / f"{file_id}.pdf"


def job_output_path(job_id: str) -> Path:
    return DATA_DIR / f"{job_id}.pdf"


def save_upload(file_id: str, data: bytes) -> Path:
    path = file_path(file_id)
    path.write_bytes(data)
    return path


def get_file(file_id: str) -> Optional[Path]:
    path = file_path(file_id)
    return path if path.exists() else None


def get_job_file(job_id: str) -> Optional[Path]:
    path = job_output_path(job_id)
    return path if path.exists() else None
