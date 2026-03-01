import React from "react";

type Level = "Low" | "Medium" | "High";

interface BadgeProps {
  level: Level;
}

const levelClassMap: Record<Level, string> = {
  Low: "ds-badge ds-badge-low",
  Medium: "ds-badge ds-badge-medium",
  High: "ds-badge ds-badge-high",
};

export function Badge({ level }: BadgeProps) {
  return (
    <span className={levelClassMap[level]}>
      <span
        className={`mr-2 h-2 w-2 rounded-full ${
          level === "High" ? "bg-rose-500" : level === "Medium" ? "bg-amber-500" : "bg-emerald-500"
        }`}
        aria-hidden="true"
      />
      {level} confidence
    </span>
  );
}

