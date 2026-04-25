"use client";

import { motion } from "framer-motion";

export default function LoadingSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass rounded-3xl p-6"
    >
      <div className="h-4 w-32 rounded-full bg-white/40" />
      <div className="mt-4 h-24 rounded-2xl bg-white/30" />
      <div className="mt-4 h-3 w-48 rounded-full bg-white/30" />
    </motion.div>
  );
}
