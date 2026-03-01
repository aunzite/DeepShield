"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { addRecent } from "@/lib/recentActivity";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/tools/deepfake", label: "Deepfake Detector" },
  { href: "/tools/headline", label: "Headline Scanner" },
  { href: "/tools/reverse-image", label: "Reverse Image Search" },
  { href: "/tools/metadata", label: "Image Metadata" },
  { href: "/tools/profile-lookup", label: "Profile Lookup" },
  { href: "/tools/link-checker", label: "Link Checker" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 flex-shrink-0 flex-col border-r border-ds-border bg-white/80 backdrop-blur-sm md:w-64">
      <div className="sticky top-0 flex flex-col p-4">
        <Link
          href="/"
          className="mb-6 font-display text-xl font-bold tracking-tight"
          style={{
            background:
              "linear-gradient(135deg, #0f766e 0%, #0d9488 40%, #0f766e 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          DeepShield
        </Link>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => {
                  if (item.href !== "/") addRecent({ path: item.href, label: item.label });
                }}
              >
                <motion.span
                  className={`block rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-teal-50 text-teal-800 shadow-sm ring-1 ring-teal-200/60"
                      : "text-ds-text-muted hover:bg-ds-card-muted/70 hover:text-ds-text"
                  }`}
                  whileHover={{ x: 2 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {item.label}
                </motion.span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
