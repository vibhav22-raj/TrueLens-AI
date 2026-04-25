"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

export default function Toast({ message }: { message: string }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 3500);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass fixed bottom-6 right-6 rounded-2xl px-4 py-3 text-sm"
    >
      {message}
    </motion.div>
  );
}
