"use client";

import axios from "axios";
import {
  GlobalWorkerOptions,
  getDocument,
  PDFDocumentProxy,
  RenderParameters,
} from "pdfjs-dist";
import workerSrc from "pdfjs-dist/build/pdf.worker.min.mjs";
import { useEffect, useMemo, useState } from "react";

GlobalWorkerOptions.workerSrc = workerSrc as string;

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

type Thumbnail = {
  pageIndex: number;
  dataUrl: string;
};

type RotationOp = { page: number; degrees: number };
type TextOp = { page: number; text: string; x: number; y: number; font_size: number; color: string };
type ImageOp = { page: number; image_data: string; x: number; y: number; width: number; height: number };
type DrawingOp =
  | { type: "line"; page: number; x1: number; y1: number; x2: number; y2: number; width: number; color: string }
  | {
      type: "rectangle";
      page: number;
      x: number;
      y: number;
      width: number;
      height: number;
      border_width: number;
      color: string;
      fill_color?: string;
    };
type RedactionOp = { page: number; x: number; y: number; width: number; height: number; fill: string };
type WatermarkOp = { text: string; size: number; opacity: number; rotation: number };

export default function HomePage() {
  const [fileId, setFileId] = useState<string | null>(null);
  const [thumbnails, setThumbnails] = useState<Thumbnail[]>([]);
  const [pageOrder, setPageOrder] = useState<number[]>([]);
  const [selectedPoint, setSelectedPoint] = useState<{ page: number; x: number; y: number } | null>(null);
  const [rotations, setRotations] = useState<RotationOp[]>([]);
  const [texts, setTexts] = useState<TextOp[]>([]);
  const [images, setImages] = useState<ImageOp[]>([]);
  const [drawings, setDrawings] = useState<DrawingOp[]>([]);
  const [deletions, setDeletions] = useState<number[]>([]);
  const [redactions, setRedactions] = useState<RedactionOp[]>([]);
  const [watermark, setWatermark] = useState<WatermarkOp | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const upload = await api.post("/api/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    const newFileId = upload.data.fileId as string;
    setFileId(newFileId);
    setStatus("Uploaded PDF");

    const buffer = await file.arrayBuffer();
    await generateThumbnails(buffer);
  };

  const generateThumbnails = async (buffer: ArrayBuffer) => {
    const pdf: PDFDocumentProxy = await getDocument({ data: buffer }).promise;
    const thumbs: Thumbnail[] = [];
    const order: number[] = [];
    for (let i = 0; i < pdf.numPages; i++) {
      const page = await pdf.getPage(i + 1);
      const viewport = page.getViewport({ scale: 0.2 });
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      if (!context) continue;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const renderContext: RenderParameters = { canvasContext: context, viewport } as RenderParameters;
      await page.render(renderContext).promise;
      thumbs.push({ pageIndex: i, dataUrl: canvas.toDataURL("image/png") });
      order.push(i);
    }
    setThumbnails(thumbs);
    setPageOrder(order);
  };

  const onDragStart = (index: number) => (event: React.DragEvent<HTMLDivElement>) => {
    event.dataTransfer.setData("text/plain", index.toString());
  };

  const onDrop = (index: number) => (event: React.DragEvent<HTMLDivElement>) => {
    const fromIndex = Number(event.dataTransfer.getData("text/plain"));
    const newOrder = [...pageOrder];
    const [removed] = newOrder.splice(fromIndex, 1);
    newOrder.splice(index, 0, removed);
    setPageOrder(newOrder);
  };

  const addRotation = (page: number, degrees: number) => {
    setRotations((prev) => [...prev, { page, degrees }]);
  };

  const addText = (text: string) => {
    if (!selectedPoint) return;
    setTexts((prev) => [
      ...prev,
      {
        page: selectedPoint.page,
        text,
        x: selectedPoint.x,
        y: selectedPoint.y,
        font_size: 14,
        color: "black",
      },
    ]);
  };

  const addRedaction = () => {
    if (!selectedPoint) return;
    setRedactions((prev) => [
      ...prev,
      { page: selectedPoint.page, x: selectedPoint.x, y: selectedPoint.y, width: 120, height: 30, fill: "black" },
    ]);
  };

  const addLine = () => {
    if (!selectedPoint) return;
    setDrawings((prev) => [
      ...prev,
      {
        type: "line",
        page: selectedPoint.page,
        x1: selectedPoint.x,
        y1: selectedPoint.y,
        x2: selectedPoint.x + 120,
        y2: selectedPoint.y + 10,
        width: 2,
        color: "red",
      },
    ]);
  };

  const addRectangle = () => {
    if (!selectedPoint) return;
    setDrawings((prev) => [
      ...prev,
      {
        type: "rectangle",
        page: selectedPoint.page,
        x: selectedPoint.x,
        y: selectedPoint.y,
        width: 140,
        height: 80,
        border_width: 2,
        color: "blue",
        fill_color: "#e0f2fe",
      },
    ]);
  };

  const handleAddImage = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedPoint) return;
    const file = event.target.files?.[0];
    if (!file) return;
    const buffer = await file.arrayBuffer();
    const binary = Array.from(new Uint8Array(buffer))
      .map((b) => String.fromCharCode(b))
      .join("");
    const b64 = btoa(binary);
    setImages((prev) => [
      ...prev,
      {
        page: selectedPoint.page,
        image_data: b64,
        x: selectedPoint.x,
        y: selectedPoint.y,
        width: 120,
        height: 80,
      },
    ]);
  };

  const handleCanvasClick = (pageIndex: number, event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    setSelectedPoint({ page: pageIndex, x, y });
  };

  const applyManifest = async () => {
    if (!fileId) return;
    const manifest: any = {};
    if (pageOrder.length) manifest.reorder = pageOrder;
    if (rotations.length) manifest.rotate = rotations;
    if (texts.length) manifest.add_text = texts;
    if (images.length) manifest.images = images;
    if (drawings.length) manifest.drawings = drawings;
    if (deletions.length) manifest.delete_pages = deletions;
    if (redactions.length) manifest.redactions = redactions;
    if (watermark) manifest.watermark = watermark;

    const resp = await api.post(`/api/files/${fileId}/apply`, manifest);
    const newJobId = resp.data.jobId as string;
    setJobId(newJobId);
    setStatus("Processing job...");

    const statusResp = await api.get(`/api/jobs/${newJobId}`);
    if (statusResp.data.status === "completed") {
      const fileResp = await api.get(`/api/jobs/${newJobId}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(fileResp.data);
      setDownloadUrl(url);
      setStatus("Completed");
    }
  };

  const manifestPreview = useMemo(
    () => ({
      reorder: pageOrder,
      rotate: rotations,
      add_text: texts,
      images,
      drawings,
      redactions,
      delete_pages: deletions,
      watermark,
    }),
    [pageOrder, rotations, texts, images, drawings, redactions, deletions, watermark]
  );

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="rounded bg-white p-4 shadow">
        <h1 className="text-2xl font-bold">PDF Editor</h1>
        <p className="text-sm text-gray-600">Upload a PDF, click on a thumbnail to set coordinates, queue edits, and generate a flattened PDF.</p>
      </header>

      <section className="rounded bg-white p-4 shadow space-y-4">
        <div className="flex items-center gap-4">
          <input type="file" accept="application/pdf" onChange={handleUpload} />
          <span className="text-sm text-gray-700">Status: {status || "Waiting"}</span>
          {downloadUrl && (
            <a className="rounded bg-blue-600 px-4 py-2 text-white" href={downloadUrl} download="edited.pdf">
              Download Edited PDF
            </a>
          )}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded bg-white p-4 shadow lg:col-span-2">
          <h2 className="mb-2 text-lg font-semibold">Pages (drag to reorder)</h2>
          <div className="flex flex-wrap gap-3">
            {thumbnails.map((thumb, idx) => (
              <div
                key={thumb.pageIndex}
                draggable
                onDragStart={onDragStart(idx)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={onDrop(idx)}
                onClick={(e) => handleCanvasClick(thumb.pageIndex, e)}
                className={`cursor-move rounded border ${selectedPoint?.page === thumb.pageIndex ? "border-blue-500" : "border-gray-200"} p-2 text-center`}
              >
                <img src={thumb.dataUrl} alt={`Page ${thumb.pageIndex + 1}`} className="h-40 w-auto" />
                <p className="text-sm text-gray-700">Page {thumb.pageIndex + 1}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4 rounded bg-white p-4 shadow">
          <h2 className="text-lg font-semibold">Tools</h2>
          <div className="space-y-2">
            <button
              onClick={() => selectedPoint && addRotation(selectedPoint.page, 90)}
              className="w-full rounded bg-indigo-600 px-3 py-2 text-white"
            >
              Rotate Selected Page 90°
            </button>
            <button
              onClick={() => selectedPoint && setDeletions((prev) => [...prev, selectedPoint.page])}
              className="w-full rounded bg-red-500 px-3 py-2 text-white"
            >
              Delete Selected Page
            </button>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add text"
                className="w-full rounded border px-2 py-1"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    addText((e.target as HTMLInputElement).value);
                    (e.target as HTMLInputElement).value = "";
                  }
                }}
              />
              <span className="rounded bg-gray-100 px-2 py-1 text-sm">click page to set point</span>
            </div>
            <button onClick={addLine} className="w-full rounded bg-gray-700 px-3 py-2 text-white">
              Draw Line from selected point
            </button>
            <button onClick={addRectangle} className="w-full rounded bg-gray-700 px-3 py-2 text-white">
              Draw Rectangle from selected point
            </button>
            <button onClick={addRedaction} className="w-full rounded bg-black px-3 py-2 text-white">
              Add Redaction at selected point
            </button>
            <div className="space-y-1">
              <label className="text-sm font-medium">Add Image (uses selected point)</label>
              <input type="file" accept="image/*" onChange={handleAddImage} />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Watermark Text</label>
              <input
                type="text"
                placeholder="CONFIDENTIAL"
                className="w-full rounded border px-2 py-1"
                onChange={(e) =>
                  setWatermark({ text: e.target.value, size: 32, opacity: 0.25, rotation: 30 })
                }
              />
            </div>
            <button onClick={applyManifest} className="w-full rounded bg-green-600 px-3 py-2 text-white">
              Apply Manifest
            </button>
            {jobId && <p className="text-xs text-gray-600">Job ID: {jobId}</p>}
          </div>
        </div>
      </section>

      <section className="rounded bg-white p-4 shadow">
        <h2 className="text-lg font-semibold">Edit Manifest Preview</h2>
        <pre className="overflow-auto whitespace-pre-wrap rounded bg-gray-100 p-3 text-sm">{JSON.stringify(manifestPreview, null, 2)}</pre>
      </section>
    </main>
  );
}
