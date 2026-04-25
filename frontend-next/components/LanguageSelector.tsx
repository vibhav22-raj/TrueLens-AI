"use client";

import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";

export default function LanguageSelector() {
  const { i18n } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-full border border-white/10 px-3 py-2 text-xs text-white"
    >
      <select
        className="bg-transparent text-white outline-none"
        value={i18n.language}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
      >
        <option value="en">English</option>
        <option value="hi">Hindi</option>
      </select>
    </motion.div>
  );
}
