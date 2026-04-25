"use client";

import { motion } from "framer-motion";

export default function AnimatedBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        className="absolute -top-40 left-1/4 h-72 w-72 rounded-full bg-rose-600/30 blur-3xl"
        animate={{ y: [0, -20, 0], x: [0, 18, 0] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-1/3 right-8 h-80 w-80 rounded-full bg-purple-700/25 blur-3xl"
        animate={{ y: [0, 26, 0], x: [0, -22, 0] }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-0 left-10 h-96 w-96 rounded-full bg-red-700/20 blur-3xl"
        animate={{ y: [0, -30, 0], x: [0, 14, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}
