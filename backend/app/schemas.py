from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, conint, confloat


class RotateOp(BaseModel):
    page: conint(ge=0)
    degrees: int = Field(..., description="Rotation in degrees (0, 90, 180, 270)")


class AddTextOp(BaseModel):
    page: conint(ge=0)
    text: str
    x: float
    y: float
    font_size: confloat(gt=0) = 12
    color: str = Field("black", description="CSS color name or hex")


class AddImageOp(BaseModel):
    page: conint(ge=0)
    image_data: str = Field(..., description="Base64-encoded image data")
    x: float
    y: float
    width: confloat(gt=0)
    height: confloat(gt=0)


class DrawLineOp(BaseModel):
    type: Literal["line"] = "line"
    page: conint(ge=0)
    x1: float
    y1: float
    x2: float
    y2: float
    width: confloat(gt=0) = 1
    color: str = "black"


class DrawRectOp(BaseModel):
    type: Literal["rectangle"] = "rectangle"
    page: conint(ge=0)
    x: float
    y: float
    width: confloat(gt=0)
    height: confloat(gt=0)
    border_width: confloat(gt=0) = 1
    color: str = "black"
    fill_color: Optional[str] = None


DrawingOp = DrawLineOp | DrawRectOp


class WatermarkOp(BaseModel):
    text: str
    size: confloat(gt=0) = 36
    opacity: confloat(gt=0, le=1) = 0.2
    rotation: float = 45


class RedactionOp(BaseModel):
    page: conint(ge=0)
    x: float
    y: float
    width: confloat(gt=0)
    height: confloat(gt=0)
    fill: str = "black"


class Manifest(BaseModel):
    reorder: Optional[List[int]] = None
    delete_pages: Optional[List[int]] = None
    rotate: Optional[List[RotateOp]] = None
    add_text: Optional[List[AddTextOp]] = None
    images: Optional[List[AddImageOp]] = None
    drawings: Optional[List[DrawingOp]] = None
    watermark: Optional[WatermarkOp] = None
    redactions: Optional[List[RedactionOp]] = None


class UploadResponse(BaseModel):
    fileId: str


class FileMetaResponse(BaseModel):
    fileId: str
    page_count: int
    page_sizes: List[tuple[float, float]]


class ApplyResponse(BaseModel):
    jobId: str


class JobStatusResponse(BaseModel):
    jobId: str
    status: Literal["pending", "processing", "completed", "failed"]
    message: Optional[str] = None
