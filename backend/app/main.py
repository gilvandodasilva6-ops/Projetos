from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .jobs import jobs
from .pdf_processor import apply_manifest
from .schemas import ApplyResponse, FileMetaResponse, JobStatusResponse, Manifest, UploadResponse
from .storage import DATA_DIR, get_file, save_upload

app = FastAPI(title="PDF Editor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
    file_id = uuid.uuid4().hex
    content = await file.read()
    save_upload(file_id, content)
    return UploadResponse(fileId=file_id)


@app.get("/api/files/{file_id}/meta", response_model=FileMetaResponse)
async def file_meta(file_id: str) -> FileMetaResponse:
    path = get_file(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")

    import fitz

    doc = fitz.open(path)
    page_sizes = [(page.rect.width, page.rect.height) for page in doc]
    return FileMetaResponse(fileId=file_id, page_count=len(doc), page_sizes=page_sizes)


@app.post("/api/files/{file_id}/apply", response_model=ApplyResponse)
async def apply(file_id: str, manifest: Manifest) -> ApplyResponse:
    path = get_file(file_id)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")

    job_id = uuid.uuid4().hex
    job = jobs.create(job_id)
    job.status = "processing"
    try:
        output_path = apply_manifest(str(path), manifest, job_id=job_id)
        jobs.set_status(job_id, "completed", file_path=output_path)
    except Exception as exc:  # pragma: no cover - unexpected failure handling
        jobs.set_status(job_id, "failed", message=str(exc))
        raise

    return ApplyResponse(jobId=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(jobId=job.job_id, status=job.status, message=job.message)


@app.get("/api/jobs/{job_id}/download")
async def job_download(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.file_path:
        raise HTTPException(status_code=400, detail="Job not completed")
    path = Path(job.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename=f"edited-{job_id}.pdf")


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "data_dir": str(DATA_DIR)}
