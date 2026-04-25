"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function GlowButton({ label, href }: { label: string; href: string }) {
  return (
    <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }}>
      <Link
        href={href}
        className="gradient-border relative inline-flex items-center justify-center rounded-full bg-ink px-8 py-3 text-sm font-semibold text-white shadow-glow"
      >
        {label}
      </Link>
    </motion.div>
  );
}
