from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Job:
    job_id: str
    status: str = "pending"
    message: Optional[str] = None
    file_path: Optional[str] = None


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}

    def create(self, job_id: str) -> Job:
        job = Job(job_id=job_id, status="pending")
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def set_status(self, job_id: str, status: str, message: Optional[str] = None, file_path: Optional[str] = None) -> None:
        job = self._jobs.get(job_id)
        if not job:
            job = self.create(job_id)
        job.status = status
        if message is not None:
            job.message = message
        if file_path is not None:
            job.file_path = file_path


jobs = JobRegistry()
