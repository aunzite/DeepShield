"use client";

import React from "react";
import { motion } from "framer-motion";

type TabKey = "image" | "headline";

interface TabsProps {
  active: TabKey;
  onChange: (tab: TabKey) => void;
}

export function Tabs({ active, onChange }: TabsProps) {
  return (
    <div className="ds-card mb-8 flex gap-2 border p-1.5 text-sm">
      <motion.button
        type="button"
        className={`ds-tab relative ${
          active === "image" ? "ds-tab-active" : "ds-tab-inactive"
        }`}
        onClick={() => onChange("image")}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        Deepfake Detector
      </motion.button>
      <motion.button
        type="button"
        className={`ds-tab relative ${
          active === "headline" ? "ds-tab-active" : "ds-tab-inactive"
        }`}
        onClick={() => onChange("headline")}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        Headline Scanner
      </motion.button>
    </div>
  );
}
