"use client";

import React, { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { API_BASE_URL, downloadReport } from "@/lib/api";
import { Loader } from "./Loader";

interface LinkCheckResponse {
  original_url: string;
  final_url: string | null;
  domain: string | null;
  status_code: number | null;
  safety_note: "safe" | "unknown" | "suspicious";
  message: string;
  redirect_count?: number;
}

export function LinkChecker() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<LinkCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please enter a URL.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await axios.post<LinkCheckResponse>(
        `${API_BASE_URL}/link-check`,
        { url: trimmed },
      );
      setResult(response.data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(
        ax.response?.data?.detail ?? "Check failed. Ensure the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  };

  const badgeClass =
    result?.safety_note === "safe"
      ? "ds-badge ds-badge-low"
      : result?.safety_note === "suspicious"
        ? "ds-badge ds-badge-high"
        : "ds-badge ds-badge-medium";

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <motion.div
        className="ds-card flex flex-col gap-4 p-6"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2 }}
      >
        <h2 className="text-lg font-semibold text-ds-text font-display">
          Link Checker
        </h2>
        <p className="text-xs text-ds-text-muted">
          Paste a URL to resolve redirects and get the final domain and status.
        </p>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/page"
          className="w-full rounded-xl border border-ds-border bg-ds-card-muted/50 px-3 py-2.5 text-sm text-ds-text placeholder:text-ds-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ds-accent focus-visible:ring-offset-2"
        />
        <motion.button
          type="button"
          className="ds-btn-primary"
          onClick={handleSubmit}
          disabled={loading}
          whileHover={loading ? {} : { scale: 1.02 }}
          whileTap={loading ? {} : { scale: 0.98 }}
        >
          {loading ? "Checking..." : "Check link"}
        </motion.button>
        {error && <p className="text-xs text-ds-danger">{error}</p>}
        {loading && !error && (
          <div className="mt-2">
            <Loader label="Resolving redirects…" />
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
          <span className={`inline-flex w-fit ${badgeClass}`}>
            {result.safety_note}
          </span>
          <p className="text-xs text-ds-text-muted">{result.message}</p>
          {result.original_url && (
            <p className="text-xs">
              <span className="text-ds-text-muted">Original: </span>
              <a
                href={result.original_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-teal-600 hover:underline"
              >
                {result.original_url}
              </a>
            </p>
          )}
          {result.final_url && (
            <p className="text-xs">
              <span className="text-ds-text-muted">Final: </span>
              <a
                href={result.final_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-teal-600 hover:underline"
              >
                {result.final_url}
              </a>
            </p>
          )}
          {result.domain && (
            <p className="text-xs text-ds-text-muted">
              Domain: <span className="text-ds-text">{result.domain}</span>
            </p>
          )}
          {result.status_code != null && (
            <p className="text-xs text-ds-text-muted">
              HTTP status: {result.status_code}
            </p>
          )}
          <button
            type="button"
            onClick={() => downloadReport(result, "link-check-report.json")}
            className="mt-2 text-xs font-medium text-teal-600 hover:underline"
          >
            Download report
          </button>
        </motion.div>
      )}
    </div>
  );
}
