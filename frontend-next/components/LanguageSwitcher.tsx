"use client";

import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass gradient-border rounded-full px-3 py-2 text-sm"
    >
      <select
        className="bg-transparent text-ink outline-none"
        value={i18n.language}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
      >
        <option value="en">English</option>
        <option value="hi">हिंदी</option>
      </select>
    </motion.div>
  );
}
