# PDF Editor App

A real PDF editor with Next.js (frontend) and FastAPI (backend) that applies edits using PyMuPDF and pikepdf. PDFs are flattened so edits open correctly in Adobe/Chrome.

## Features
- Upload PDF and preview thumbnails (pdf.js)
- Drag & drop reorder, rotate, delete pages
- Add text, images, lines, rectangles
- Watermark text
- Real redaction (content removed) and flattening
- Download edited PDF via job endpoint

## API
- `POST /api/upload` -> `{ fileId }`
- `GET /api/files/{fileId}/meta` -> page count + sizes
- `POST /api/files/{fileId}/apply` -> manifest -> `{ jobId }`
- `GET /api/jobs/{jobId}` -> status
- `GET /api/jobs/{jobId}/download` -> edited PDF

## Running locally

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### Docker Compose
```bash
docker-compose up --build
```
Frontend at `http://localhost:3000`, backend at `http://localhost:8000`.

## Tests
Run pytest from backend:
```bash
cd backend
pytest
```
