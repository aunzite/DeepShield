"use client";

import React, { useMemo, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Loader } from "./Loader";
import { API_BASE_URL, downloadReport } from "@/lib/api";

/** Single match from the detector: phrase, category, weight */
interface HeadlineMatch {
  phrase: string;
  category: string;
  weight: number;
}

interface HeadlineAnalysisResponse {
  manipulation_score: number;
  risk_level: "Low" | "Moderate" | "High" | "Extreme";
  flagged_phrases: string[];
  summary: string;
  clickbait_score: number;
  matches: HeadlineMatch[];
  category_breakdown: Record<string, number>;
}

function getRiskBadgeClass(
  level: "Low" | "Moderate" | "High" | "Extreme"
): string {
  if (level === "Extreme") return "ds-badge ds-badge-high";
  if (level === "High") return "ds-badge ds-badge-high";
  if (level === "Moderate") return "ds-badge ds-badge-medium";
  return "ds-badge ds-badge-low";
}

/**
 * Build highlighted headline segments from headline text and matched phrases.
 * Uses match positions to avoid redundant scans; merges overlapping spans.
 */
function buildHighlightedSegments(
  headline: string,
  matches: HeadlineMatch[]
): React.ReactNode[] {
  if (!headline || matches.length === 0) {
    return [<span key="full">{headline}</span>];
  }
  const spans: { start: number; end: number }[] = [];
  const lower = headline.toLowerCase();
  for (const m of matches) {
    const phrase = m.phrase;
    let idx = 0;
    while (idx < headline.length) {
      const found = lower.indexOf(phrase.toLowerCase(), idx);
      if (found === -1) break;
      spans.push({ start: found, end: found + phrase.length });
      idx = found + 1;
    }
  }
  // Sort by start, then merge overlapping
  spans.sort((a, b) => a.start - b.start);
  const merged: { start: number; end: number }[] = [];
  for (const s of spans) {
    if (merged.length && s.start <= merged[merged.length - 1].end) {
      merged[merged.length - 1].end = Math.max(
        merged[merged.length - 1].end,
        s.end
      );
    } else {
      merged.push({ ...s });
    }
  }
  const segments: React.ReactNode[] = [];
  let pos = 0;
  for (const { start, end } of merged) {
    if (start > pos) {
      segments.push(
        <span key={`t-${pos}`}>{headline.slice(pos, start)}</span>
      );
    }
    segments.push(
      <span
        key={`m-${start}`}
        className="rounded bg-rose-100 px-1.5 py-0.5 text-rose-800 underline decoration-rose-300 decoration-2"
      >
        {headline.slice(start, end)}
      </span>
    );
    pos = end;
  }
  if (pos < headline.length) {
    segments.push(<span key={`t-${pos}`}>{headline.slice(pos)}</span>);
  }
  return segments.length ? segments : [<span key="full">{headline}</span>];
}

export function HeadlineAnalyzer() {
  const [headline, setHeadline] = useState("");
  const [result, setResult] = useState<HeadlineAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    const trimmed = headline.trim();
    if (!trimmed) {
      setError("Please paste a headline to analyze.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await axios.post<HeadlineAnalysisResponse>(
        `${API_BASE_URL}/analyze-headline`,
        { headline: trimmed },
      );
      setResult(response.data);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(
        ax.response?.data?.detail ??
          "Failed to analyze headline. Please ensure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const manipulationPercent = result
    ? (result.manipulation_score * 100).toFixed(1)
    : "0.0";

  const highlightedSegments = useMemo(() => {
    if (!headline) return null;
    if (result && result.matches && result.matches.length > 0) {
      return buildHighlightedSegments(headline, result.matches);
    }
    return [<span key="full">{headline}</span>];
  }, [headline, result?.matches]);

  const hasBreakdown =
    result?.category_breakdown &&
    Object.keys(result.category_breakdown).length > 0;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <motion.div
        className="ds-card flex flex-col gap-4 p-6"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2 }}
      >
        <h2 className="text-lg font-semibold text-ds-text font-display">
          Headline Scanner
        </h2>
        <p className="text-xs text-ds-text-muted">
          Paste a news or social headline to check for clickbait and
          misinformation. DeepShield uses weighted categories (urgency, emotion,
          conspiracy framing, scam language, absolute claims, fake authority) and
          highlights matched phrases in red.
        </p>
        <div className="mt-2">
          <textarea
            rows={4}
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="Example: BREAKING: You won't believe what scientists just discovered about AI..."
            className="w-full rounded-xl border border-ds-border bg-ds-card-muted/50 px-3 py-2 text-sm text-ds-text placeholder:text-ds-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ds-accent focus-visible:ring-offset-2"
          />
        </div>
        <div className="mt-2 flex items-center justify-between gap-4">
          <motion.button
            type="button"
            className="ds-btn-primary"
            onClick={handleAnalyze}
            disabled={loading}
            whileHover={loading ? {} : { scale: 1.02 }}
            whileTap={loading ? {} : { scale: 0.98 }}
          >
            {loading ? "Analyzing..." : "Analyze Headline"}
          </motion.button>
          {result && (
            <motion.span
              className={getRiskBadgeClass(result.risk_level)}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25 }}
            >
              {result.risk_level} risk
            </motion.span>
          )}
        </div>
        {error && <p className="mt-2 text-xs text-ds-danger">{error}</p>}
        {loading && !error && (
          <div className="mt-3">
            <Loader label="Scanning for manipulation signals…" />
          </div>
        )}
        {result && (
          <motion.div
            className="mt-4 space-y-3 text-sm"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-ds-text">
                <span className="font-semibold text-ds-text">
                  Clickbait score:
                </span>{" "}
                <span className="text-ds-accent font-medium">
                  {result.clickbait_score}
                </span>
              </p>
              <p className="text-ds-text-muted text-xs">
                <span className="font-semibold text-ds-text">
                  Manipulation:
                </span>{" "}
                {manipulationPercent}%
              </p>
            </div>
            <div className="rounded-xl bg-ds-card-muted/70 p-3 text-xs leading-relaxed text-ds-text-muted">
              {result.summary}
            </div>
            {hasBreakdown && (
              <div className="text-xs">
                <p className="mb-1.5 font-semibold text-ds-text">
                  Category breakdown
                </p>
                <table className="w-full border-collapse rounded-lg border border-ds-border bg-white">
                  <thead>
                    <tr className="border-b border-ds-border bg-ds-card-muted/50">
                      <th className="px-2 py-1.5 text-left font-medium text-ds-text">
                        Category
                      </th>
                      <th className="px-2 py-1.5 text-right font-medium text-ds-text">
                        Points
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(result.category_breakdown).map(
                      ([cat, points]) => (
                        <tr
                          key={cat}
                          className="border-b border-ds-border last:border-0"
                        >
                          <td className="px-2 py-1.5 text-ds-text-muted">
                            {cat}
                          </td>
                          <td className="px-2 py-1.5 text-right font-medium text-ds-text">
                            {points}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            )}
            {result.flagged_phrases.length > 0 && (
              <div className="text-xs text-ds-text-muted">
                <p className="font-semibold text-ds-text">Flagged phrases</p>
                <ul className="mt-1 flex flex-wrap gap-2">
                  {result.flagged_phrases.map((p) => (
                    <li
                      key={p}
                      className="rounded-full border border-rose-200 bg-rose-100 px-2.5 py-0.5 text-[11px] text-rose-800"
                    >
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <button
              type="button"
              onClick={() => downloadReport(result, "headline-report.json")}
              className="mt-2 text-xs font-medium text-teal-600 hover:underline"
            >
              Download report
            </button>
          </motion.div>
        )}
      </motion.div>
      <motion.div
        className="ds-card flex flex-col gap-4 p-6"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2 }}
      >
        <h3 className="text-sm font-semibold tracking-wide text-ds-text font-display">
          Highlighted Headline
        </h3>
        <p className="text-xs text-ds-text-muted">
          Matched phrases from the detector are highlighted in red. Score and
          category breakdown appear in the left panel after analysis.
        </p>
        <div className="mt-2 flex-1 rounded-xl bg-ds-card-muted/70 p-4 text-sm text-ds-text">
          {headline ? (
            <p className="leading-relaxed">{highlightedSegments}</p>
          ) : (
            <p className="text-xs text-ds-text-muted">
              Paste a headline on the left and click Analyze to see highlighted
              phrases here.
            </p>
          )}
        </div>
      </motion.div>
    </div>
  );
}
