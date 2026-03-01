"use client";

import React from "react";
import { motion } from "framer-motion";

interface LoaderProps {
  label?: string;
}

export function Loader({ label }: LoaderProps) {
  return (
    <motion.div
      className="flex items-center gap-3 text-sm text-ds-text-muted"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      <motion.span
        className="h-4 w-4 flex-shrink-0 rounded-full border-2 border-teal-500 border-t-transparent"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
      />
      <span>{label ?? "Loading..."}</span>
    </motion.div>
  );
}

