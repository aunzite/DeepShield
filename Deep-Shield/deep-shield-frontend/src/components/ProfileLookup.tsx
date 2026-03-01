"use client";

import React, { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { API_BASE_URL, downloadReport } from "@/lib/api";
import { Loader } from "./Loader";

interface ProfileLookupResponse {
  profile_url: string;
  display_name: string | null;
  description: string | null;
  location_hints: string[];
  profile_image_url: string | null;
  disclaimer?: string;
  error?: string;
}

export function ProfileLookup() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<ProfileLookupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please enter a profile URL.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await axios.post<ProfileLookupResponse>(
        `${API_BASE_URL}/profile-lookup`,
        { url: trimmed },
      );
      setResult(response.data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(
        ax.response?.data?.detail ??
          "Lookup failed. Ensure the backend is running.",
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
          Profile Lookup
        </h2>
        <p className="text-xs text-ds-text-muted">
          Paste a profile URL (e.g. Twitter, Instagram, LinkedIn) to see public
          info and location hints from Open Graph and page metadata.
        </p>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://twitter.com/username or https://linkedin.com/in/username"
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
          {loading ? "Looking up..." : "Look up"}
        </motion.button>
        {error && <p className="text-xs text-ds-danger">{error}</p>}
        {loading && !error && (
          <div className="mt-2">
            <Loader label="Fetching profile…" />
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

          {result.error ? (
            <p className="text-xs text-ds-danger">{result.error}</p>
          ) : (
            <>
              {result.profile_image_url && (
                <img
                  src={result.profile_image_url}
                  alt="Profile"
                  className="h-20 w-20 rounded-full object-cover"
                />
              )}
              {result.display_name && (
                <p className="font-medium text-ds-text">
                  {result.display_name}
                </p>
              )}
              <a
                href={result.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-teal-600 hover:underline"
              >
                {result.profile_url}
              </a>
              {result.description && (
                <p className="text-xs text-ds-text-muted">
                  {result.description}
                </p>
              )}
              {result.location_hints.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-ds-text">
                    Location hints
                  </p>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {result.location_hints.map((hint, i) => (
                      <li
                        key={i}
                        className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs text-teal-800"
                      >
                        {hint}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {result.disclaimer && (
            <p className="mt-2 border-t border-ds-border pt-2 text-[10px] text-ds-text-muted">
              {result.disclaimer}
            </p>
          )}
          <button
            type="button"
            onClick={() => downloadReport(result, "profile-lookup-report.json")}
            className="mt-2 text-xs font-medium text-teal-600 hover:underline"
          >
            Download report
          </button>
        </motion.div>
      )}
    </div>
  );
}
