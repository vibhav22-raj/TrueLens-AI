"use client";

import { Moon, Sun } from "lucide-react";
import { motion } from "framer-motion";
import { useTheme } from "@/components/ThemeContext";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="glass gradient-border relative flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold"
      aria-label="Toggle theme"
    >
      <motion.span
        key={theme}
        initial={{ rotate: -90, opacity: 0 }}
        animate={{ rotate: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="text-ink"
      >
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </motion.span>
      <span>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
