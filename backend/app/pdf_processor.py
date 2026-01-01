from __future__ import annotations

import base64
import io
from typing import List

import fitz  # PyMuPDF
import pikepdf

from .schemas import (
    AddImageOp,
    AddTextOp,
    Manifest,
    RedactionOp,
    RotateOp,
    WatermarkOp,
    DrawingOp,
)
from .storage import job_output_path


RGB_COLOR_MAP = {
    "black": (0, 0, 0),
    "red": (1, 0, 0),
    "green": (0, 1, 0),
    "blue": (0, 0, 1),
    "white": (1, 1, 1),
}


def _color_from_string(color: str) -> tuple[float, float, float]:
    if color.startswith("#") and len(color) in {4, 7}:
        hex_value = color.lstrip("#")
        if len(hex_value) == 3:
            hex_value = "".join(c * 2 for c in hex_value)
        r, g, b = (int(hex_value[i : i + 2], 16) / 255 for i in (0, 2, 4))
        return (r, g, b)
    return RGB_COLOR_MAP.get(color.lower(), (0, 0, 0))


def _apply_reorder(doc: fitz.Document, order: List[int]) -> fitz.Document:
    new_doc = fitz.open()
    for idx in order:
        new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
    return new_doc


def _apply_delete(doc: fitz.Document, delete_pages: List[int]) -> None:
    for idx in sorted(delete_pages, reverse=True):
        doc.delete_page(idx)


def _apply_rotate(doc: fitz.Document, rotations: List[RotateOp]) -> None:
    for rot in rotations:
        page = doc.load_page(rot.page)
        page.set_rotation(rot.degrees)


def _apply_add_text(doc: fitz.Document, texts: List[AddTextOp]) -> None:
    for item in texts:
        page = doc.load_page(item.page)
        color = _color_from_string(item.color)
        page.insert_text((item.x, item.y), item.text, fontsize=item.font_size, color=color)


def _apply_images(doc: fitz.Document, images: List[AddImageOp]) -> None:
    for img in images:
        page = doc.load_page(img.page)
        image_bytes = base64.b64decode(img.image_data)
        stream = io.BytesIO(image_bytes)
        rect = fitz.Rect(img.x, img.y, img.x + img.width, img.y + img.height)
        page.insert_image(rect, stream=stream)


def _apply_drawings(doc: fitz.Document, drawings: List[DrawingOp]) -> None:
    for drawing in drawings:
        page = doc.load_page(drawing.page)
        if drawing.type == "line":
            color = _color_from_string(drawing.color)
            page.draw_line((drawing.x1, drawing.y1), (drawing.x2, drawing.y2), color=color, width=drawing.width)
        elif drawing.type == "rectangle":
            color = _color_from_string(drawing.color)
            fill_color = _color_from_string(drawing.fill_color) if drawing.fill_color else None
            rect = fitz.Rect(drawing.x, drawing.y, drawing.x + drawing.width, drawing.y + drawing.height)
            page.draw_rect(rect, color=color, fill=fill_color, width=drawing.border_width)


def _apply_watermark(doc: fitz.Document, watermark: WatermarkOp) -> None:
    for page in doc:
        color_value = 1 - (watermark.opacity * 0.5)
        color = (color_value, color_value, color_value)
        page.insert_textbox(
            page.rect,
            watermark.text,
            fontsize=watermark.size,
            rotate=watermark.rotation,
            color=color,
            overlay=True,
            fill=color,
            align=fitz.TEXT_ALIGN_CENTER,
            render_mode=0,
        )


def _apply_redactions(doc: fitz.Document, redactions: List[RedactionOp]) -> None:
    for redaction in redactions:
        page = doc.load_page(redaction.page)
        rect = fitz.Rect(redaction.x, redaction.y, redaction.x + redaction.width, redaction.y + redaction.height)
        page.add_redact_annot(rect, fill=_color_from_string(redaction.fill))
    for page in doc:
        page.apply_redactions()


def apply_manifest(input_path: str, manifest: Manifest, job_id: str) -> str:
    doc = fitz.open(input_path)

    if manifest.delete_pages:
        _apply_delete(doc, manifest.delete_pages)
    if manifest.reorder:
        doc = _apply_reorder(doc, manifest.reorder)
    if manifest.rotate:
        _apply_rotate(doc, manifest.rotate)
    if manifest.add_text:
        _apply_add_text(doc, manifest.add_text)
    if manifest.images:
        _apply_images(doc, manifest.images)
    if manifest.drawings:
        _apply_drawings(doc, manifest.drawings)
    if manifest.watermark:
        _apply_watermark(doc, manifest.watermark)
    if manifest.redactions:
        _apply_redactions(doc, manifest.redactions)

    temp_pdf = io.BytesIO(doc.tobytes(deflate=True, garbage=3, clean=True))

    # Use pikepdf to linearize and ensure final file is clean
    with pikepdf.open(temp_pdf) as pdf:
        output_path = job_output_path(job_id)
        pdf.save(output_path, linearize=True, optimize_version=True)

    return str(output_path)
