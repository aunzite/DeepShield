"use client";

import React from "react";

/** Honest indeterminate progress: shows activity only, no fake percentage. */
interface ProgressBarProps {
  active: boolean;
  label?: string;
  onComplete?: () => void;
}

export function ProgressBar({ active, label }: ProgressBarProps) {
  if (!active) return null;

  return (
    <div className="w-full space-y-1.5">
      <div className="text-xs text-ds-text-muted">
        {label ?? "Loading..."}
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-ds-card-muted">
        <div className="ds-progress-indeterminate h-full w-full rounded-full" />
      </div>
    </div>
  );
}
