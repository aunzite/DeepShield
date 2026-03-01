"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Tabs } from "@/components/Tabs";
import { ImageAnalyzer } from "@/components/ImageAnalyzer";
import { HeadlineAnalyzer } from "@/components/HeadlineAnalyzer";

type TabKey = "image" | "headline";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

export default function HomePage() {
  const [active, setActive] = useState<TabKey>("image");

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-12 pt-10 md:px-8 lg:px-10">
      <motion.header
        className="mb-10 flex flex-col gap-6 md:flex-row md:items-center md:justify-between"
        variants={container}
        initial="hidden"
        animate="show"
      >
        <div>
          <motion.h1
            variants={item}
            className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl"
            style={{
              background:
                "linear-gradient(135deg, #0f766e 0%, #0d9488 40%, #0f766e 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            DeepShield
          </motion.h1>
          <motion.p
            variants={item}
            className="mt-3 max-w-xl text-sm text-ds-text-muted sm:text-base"
          >
            <span className="font-semibold bg-gradient-to-r from-teal-600 to-teal-500 bg-clip-text text-transparent">
              AI-Powered Digital Safety Toolkit
            </span>{" "}
            — check images and headlines. Deepfake Detector and Headline Scanner.
          </motion.p>
        </div>
        <motion.div
          variants={item}
          className="ds-card max-w-xs border-l-4 border-l-teal-500/60 p-4 text-xs text-ds-text-muted"
        >
          <p className="font-semibold text-ds-text">How to use</p>
          <ul className="mt-2 list-disc space-y-1 pl-4">
            <li>Upload a profile photo or generated face to compare scores.</li>
            <li>Paste a dramatic news headline to highlight buzzwords.</li>
          </ul>
        </motion.div>
      </motion.header>

      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
      >
        <Tabs active={active} onChange={setActive} />
        <AnimatePresence mode="wait">
          {active === "image" ? (
            <motion.div
              key="image"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
            >
              <ImageAnalyzer />
            </motion.div>
          ) : (
            <motion.div
              key="headline"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
            >
              <HeadlineAnalyzer />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.section>
    </main>
  );
}
