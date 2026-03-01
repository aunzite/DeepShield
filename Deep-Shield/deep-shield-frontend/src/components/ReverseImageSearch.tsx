"use client";

import React, { useCallback, useRef, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { API_BASE_URL, downloadReport } from "@/lib/api";
import { Loader } from "./Loader";

interface ReverseSearchResult {
  url: string;
  title?: string;
  image_url?: string;
}

interface ReverseSearchResponse {
  configured: boolean;
  message: string;
  results: ReverseSearchResult[];
  manual_links?: { tineye: string; google_images: string };
}

export function ReverseImageSearch() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ReverseSearchResponse | null>(null);
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
      const response = await axios.post<ReverseSearchResponse>(
        `${API_BASE_URL}/reverse-image-search`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setResult(response.data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(
        ax.response?.data?.detail ??
          "Reverse search failed. Ensure the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <motion.div
        className="ds-card flex flex-col gap-4 p-6"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2 }}
      >
        <h2 className="text-lg font-semibold text-ds-text font-display">
          Reverse Image Search
        </h2>
        <p className="text-xs text-ds-text-muted">
          Upload an image to see if it appears elsewhere on the web (e.g. to
          check if a photo was taken from somewhere else).
        </p>
        <motion.div
          className={`mt-2 flex flex-1 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-4 py-10 text-center ${
            isDragOver
              ? "border-ds-accent bg-ds-card-muted"
              : "border-ds-border bg-ds-card-muted/50 hover:border-ds-accent hover:bg-ds-card-muted"
          }`}
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
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
              <span className="text-3xl">🔍</span>
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
            id="reverse-upload"
            type="file"
            accept="image/*"
            className="sr-only"
            aria-label="Choose image file"
            onChange={handleFileInput}
          />
          <label
            htmlFor="reverse-upload"
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
          {loading ? "Searching..." : "Search"}
        </motion.button>
        {error && <p className="text-xs text-ds-danger">{error}</p>}
        {loading && !error && (
          <div className="mt-2">
            <Loader label="Searching for matches…" />
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
          <p className="text-xs text-ds-text-muted">{result.message}</p>

          {result.results.length > 0 ? (
            <ul className="space-y-2">
              {result.results.map((r, i) => (
                <li key={i}>
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg border border-ds-border bg-ds-card-muted/50 p-3 text-sm text-teal-600 hover:bg-ds-card-muted hover:underline"
                  >
                    <span className="font-medium">
                      {r.title || r.url || "Link"}
                    </span>
                    <span className="ml-2 text-xs text-ds-text-muted">
                      Open →
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          ) : null}

          {result.manual_links && (
            <div className="mt-4 border-t border-ds-border pt-4">
              <p className="mb-2 text-xs font-medium text-ds-text">
                Check manually
              </p>
              <div className="flex flex-wrap gap-2">
                <a
                  href={result.manual_links.tineye}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-full bg-ds-card-muted px-3 py-1.5 text-xs font-medium text-teal-600 hover:bg-teal-50"
                >
                  TinEye
                </a>
                <a
                  href={result.manual_links.google_images}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-full bg-ds-card-muted px-3 py-1.5 text-xs font-medium text-teal-600 hover:bg-teal-50"
                >
                  Google Images
                </a>
              </div>
            </div>
          )}
          <button
            type="button"
            onClick={() => downloadReport(result, "reverse-search-report.json")}
            className="mt-2 text-xs font-medium text-teal-600 hover:underline"
          >
            Download report
          </button>
        </motion.div>
      )}
    </div>
  );
}
