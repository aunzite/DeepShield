"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ChartOptions,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Badge } from "./Badge";
import { Loader } from "./Loader";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface ImageAnalysisResponse {
  real_probability?: number;
  fake_probability?: number;
  confidence_level?: "Low" | "Medium" | "High";
  error?: string;
}

import { API_BASE_URL, downloadReport } from "@/lib/api";

const DEEPFAKE_STEPS = [
  "Opening image…",
  "Detecting face…",
  "Running deepfake model…",
  "Almost done…",
];

export function ImageAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ImageAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!loading) {
      setLoadingStep(0);
      return;
    }
    const last = DEEPFAKE_STEPS.length - 1;
    const interval = setInterval(() => {
      setLoadingStep((s) => (s >= last ? last : s + 1));
    }, 2200);
    return () => clearInterval(interval);
  }, [loading]);

  const onFileChange = useCallback((f: File | null) => {
    setFile(f);
    setResult(null);
    setError(null);
    if (f) {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  }, []);

  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const f = event.target.files?.[0];
    if (f) {
      onFileChange(f);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const f = event.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) {
      onFileChange(f);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please upload an image to analyze.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await axios.post<ImageAnalysisResponse>(
        `${API_BASE_URL}/analyze-image`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );
      if (response.data.error) {
        setError(response.data.error);
        setResult(null);
      } else {
        setError(null);
        setResult(response.data);
      }
    } catch (err: any) {
      const message =
        err.response?.data?.detail ??
        "Failed to analyze image. Please ensure the backend is running.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const fakeProb = result?.fake_probability ?? 0;
  const realProb = result?.real_probability ?? 0;
  const chartData = {
    labels: ["AI-generated", "Human-created"],
    datasets: [
      {
        label: "Probability",
        data: [fakeProb * 100, realProb * 100],
        backgroundColor: ["#0d9488", "rgba(224, 124, 94, 0.5)"],
        borderRadius: 8,
      },
    ],
  };

  const chartOptions: ChartOptions<"bar"> = {
    responsive: true,
    animation: {
      duration: 800,
    },
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          color: "#2d2a26",
        },
      },
      title: {
        display: true,
        text: "AI vs Human Probability",
        color: "#2d2a26",
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `${context.parsed.y.toFixed(1)}%`,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#6b6560",
        },
        grid: {
          color: "rgba(45, 42, 38, 0.08)",
        },
      },
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          color: "#6b6560",
          callback: (value: number | string) => `${value}%`,
        },
        grid: {
          color: "rgba(45, 42, 38, 0.08)",
        },
      },
    },
  };

  const probabilityPercentage = (fakeProb * 100).toFixed(1);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <motion.div
        className="ds-card flex flex-col gap-4 p-6"
        whileHover={{ y: -2 }}
        transition={{ duration: 0.2 }}
      >
        <h2 className="text-lg font-semibold text-ds-text font-display">
          Deepfake Detector
        </h2>
        <p className="text-xs text-ds-text-muted">
          This tool detects facial manipulation artifacts using a
          deepfake-trained model. It is designed to analyze human faces and may
          not work on non-face images.
        </p>
        <motion.div
          className={`mt-2 flex flex-1 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-4 py-10 text-center ${
            isDragOver ? "border-ds-accent bg-ds-card-muted" : "border-ds-border bg-ds-card-muted/50 hover:border-ds-accent hover:bg-ds-card-muted"
          }`}
          animate={{ scale: isDragOver ? 1.01 : 1 }}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          transition={{ duration: 0.15 }}
        >
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Preview"
              className="mb-4 max-h-64 rounded-xl object-contain"
            />
          ) : (
            <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-ds-card-muted text-ds-accent">
              <span className="text-3xl">🛡️</span>
            </div>
          )}
          <p className="text-sm font-medium text-ds-text">
            Drag &amp; drop an image here
          </p>
          <p className="mt-1 text-xs text-ds-text-muted">
            or choose a file from your device
          </p>
          <input
            ref={fileInputRef}
            id="image-upload"
            type="file"
            accept="image/*"
            className="sr-only"
            aria-label="Choose image file"
            onChange={handleFileInput}
          />
          <label
            htmlFor="image-upload"
            className="ds-file-btn mt-4 cursor-pointer"
          >
            <span aria-hidden>📁</span>
            Choose file
          </label>
        </motion.div>
        <div className="mt-4 flex items-center justify-between gap-4">
          <motion.button
            type="button"
            className="ds-btn-primary"
            onClick={handleSubmit}
            disabled={loading}
            whileHover={loading ? {} : { scale: 1.02 }}
            whileTap={loading ? {} : { scale: 0.98 }}
          >
            {loading ? "Analyzing..." : "Analyze Image"}
          </motion.button>
          {result && result.confidence_level && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25 }}
            >
              <Badge level={result.confidence_level} />
            </motion.div>
          )}
        </div>
        {error && (
          <p className="mt-2 text-xs text-ds-danger">
            {error}
          </p>
        )}
        {loading && !error && (
          <div className="mt-3">
            <Loader label={DEEPFAKE_STEPS[loadingStep]} />
          </div>
        )}
        {result && (
          <motion.div
            className="mt-4 space-y-2 text-sm"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <p className="text-ds-text">
              <span className="font-semibold text-ds-text">
                Manipulation (fake) probability:
              </span>{" "}
              <span className="text-ds-accent font-medium">{probabilityPercentage}%</span>
            </p>
            <p className="text-xs leading-relaxed text-ds-text-muted">
              Real face probability: {(realProb * 100).toFixed(1)}%. This result
              is from a model trained on real vs. deepfake face data.
            </p>
            <button
              type="button"
              onClick={() => downloadReport(result, "deepfake-report.json")}
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
          Model Insight
        </h3>
        <p className="text-xs text-ds-text-muted">
          This visualization shows the probability that the detected face is
          AI-generated or manipulated (fake) versus human-created (real), from a
          deepfake-trained model. Results are assistive only.
        </p>
        <div className="mt-2 flex-1 rounded-xl bg-ds-card-muted/70 p-3">
          <Bar data={chartData} options={chartOptions} />
        </div>
      </motion.div>
    </div>
  );
}

