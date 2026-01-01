from io import BytesIO

import fitz
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _sample_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4-like
    page.insert_text((72, 72), "Hello World", fontsize=16)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_apply_manifest_flow(tmp_path):
    pdf_bytes = _sample_pdf_bytes()
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["fileId"]

    manifest = {
        "rotate": [{"page": 0, "degrees": 90}],
        "add_text": [
            {
                "page": 0,
                "text": "Added Note",
                "x": 200,
                "y": 200,
                "font_size": 14,
                "color": "blue",
            }
        ],
        "watermark": {"text": "CONFIDENTIAL", "size": 24, "opacity": 0.3, "rotation": 30},
        "redactions": [
            {"page": 0, "x": 60, "y": 60, "width": 150, "height": 30, "fill": "white"}
        ],
    }

    apply_resp = client.post(f"/api/files/{file_id}/apply", json=manifest)
    assert apply_resp.status_code == 200
    job_id = apply_resp.json()["jobId"]

    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"

    download_resp = client.get(f"/api/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    result_pdf = download_resp.content

    processed = fitz.open(stream=result_pdf, filetype="pdf")
    page = processed.load_page(0)

    assert page.rotation == 90

    text_content = page.get_text()
    assert "Added Note" in text_content
    assert "CONFIDENTIAL" in text_content
    assert "Hello World" not in text_content  # redaction should remove original text
