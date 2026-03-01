"use client";

import React, { useCallback, useRef, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { API_BASE_URL, downloadReport } from "@/lib/api";
import { Loader } from "./Loader";

interface MetadataResponse {
  basic: {
    format?: string;
    width: number;
    height: number;
    mode?: string;
    size_bytes?: number;
  };
  exif: Record<string, string> | null;
  gps: { lat: number; lon: number } | null;
}

export function MetadataAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<MetadataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onFileChange = useCallback((f: File | null) => {
    setFile(f);
    setResult(null);
    setError(null);
    if (f) {
      setPreviewUrl(URL.createObjectURL(f));
    } else {
      setPreviewUrl(null);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) onFileChange(f);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) onFileChange(f);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please upload an image.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await axios.post<MetadataResponse>(
        `${API_BASE_URL}/image-metadata`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setResult(response.data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(
        ax.response?.data?.detail ??
          "Failed to read metadata. Ensure the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  };

  const mapUrl = result?.gps
    ? `https://www.openstreetmap.org/?mlat=${result.gps.lat}&mlon=${result.gps.lon}&zoom=14`
    : null;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <motion.div
        className="ds-card flex flex-col gap-4 p-6"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2 }}
      >
        <h2 className="text-lg font-semibold text-ds-text font-display">
          Image Metadata
        </h2>
        <p className="text-xs text-ds-text-muted">
          Upload an image to reveal EXIF and other metadata (camera, date,
          location if present). Sharing images can leak this data.
        </p>
        <motion.div
          className={`mt-2 flex flex-1 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-4 py-10 text-center ${
            isDragOver
              ? "border-ds-accent bg-ds-card-muted"
              : "border-ds-border bg-ds-card-muted/50 hover:border-ds-accent hover:bg-ds-card-muted"
          }`}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
        >
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Preview"
              className="mb-4 max-h-64 rounded-xl object-contain"
            />
          ) : (
            <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-ds-card-muted text-ds-accent">
              <span className="text-3xl">📋</span>
            </div>
          )}
          <p className="text-sm font-medium text-ds-text">
            Drag & drop an image here
          </p>
          <p className="mt-1 text-xs text-ds-text-muted">
            or choose a file from your device
          </p>
          <input
            ref={fileInputRef}
            id="metadata-upload"
            type="file"
            accept="image/*"
            className="sr-only"
            aria-label="Choose image file"
            onChange={handleFileInput}
          />
          <label
            htmlFor="metadata-upload"
            className="ds-file-btn mt-4 cursor-pointer"
          >
            Choose file
          </label>
        </motion.div>
        <motion.button
          type="button"
          className="ds-btn-primary mt-2"
          onClick={handleSubmit}
          disabled={loading}
          whileHover={loading ? {} : { scale: 1.02 }}
          whileTap={loading ? {} : { scale: 0.98 }}
        >
          {loading ? "Reading..." : "Reveal Metadata"}
        </motion.button>
        {error && (
          <p className="text-xs text-ds-danger">{error}</p>
        )}
        {loading && !error && (
          <div className="mt-2">
            <Loader label="Reading image metadata…" />
          </div>
        )}
      </motion.div>

      {result && (
        <motion.div
          className="ds-card flex flex-col gap-4 p-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h3 className="text-sm font-semibold text-ds-text font-display">
            Result
          </h3>

          <div className="space-y-4 text-sm">
            <div>
              <p className="font-semibold text-ds-text">Basic</p>
              <ul className="mt-1 rounded-xl bg-ds-card-muted/70 p-3 text-xs text-ds-text-muted">
                <li>Format: {result.basic.format ?? "—"}</li>
                <li>Dimensions: {result.basic.width} × {result.basic.height}</li>
                <li>Mode: {result.basic.mode ?? "—"}</li>
                {result.basic.size_bytes != null && (
                  <li>Size: {(result.basic.size_bytes / 1024).toFixed(1)} KB</li>
                )}
              </ul>
            </div>

            {result.exif && Object.keys(result.exif).length > 0 && (
              <div>
                <p className="font-semibold text-ds-text">EXIF</p>
                <ul className="mt-1 max-h-48 space-y-1 overflow-y-auto rounded-xl bg-ds-card-muted/70 p-3 text-xs text-ds-text-muted">
                  {Object.entries(result.exif).map(([k, v]) => (
                    <li key={k}>
                      <span className="text-ds-text">{k}:</span> {v}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.gps && (
              <div>
                <p className="font-semibold text-ds-text">GPS</p>
                <div className="mt-1 rounded-xl bg-ds-card-muted/70 p-3 text-xs text-ds-text-muted">
                  <p>
                    {result.gps.lat}, {result.gps.lon}
                  </p>
                  {mapUrl && (
                    <a
                      href={mapUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block font-medium text-teal-600 hover:underline"
                    >
                      View on map →
                    </a>
                  )}
                </div>
              </div>
            )}

            {(!result.exif || Object.keys(result.exif).length === 0) &&
              !result.gps && (
                <p className="text-xs text-ds-text-muted">
                  No EXIF or GPS data found in this image.
                </p>
              )}
            <button
              type="button"
              onClick={() => downloadReport(result, "metadata-report.json")}
              className="mt-2 text-xs font-medium text-teal-600 hover:underline"
            >
              Download report
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
