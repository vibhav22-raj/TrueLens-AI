"use client";

import { motion } from "framer-motion";
import GlowButton from "@/components/GlowButton";
import { useTranslation } from "react-i18next";

export default function HeroSection() {
  const { t } = useTranslation();

  return (
    <section className="relative flex flex-col gap-8 px-6 py-20 md:px-16">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-3xl"
      >
        <p className="mb-4 text-sm uppercase tracking-[0.3em] text-ink/60">DeepShield AI</p>
        <h1 className="text-4xl font-semibold md:text-6xl">
          <span className="gradient-text">{t("hero.title")}</span>
        </h1>
        <p className="mt-6 text-lg text-ink/70 md:text-xl">{t("hero.subtitle")}</p>
        <div className="mt-10 flex flex-wrap gap-4">
          <GlowButton href="/dashboard/upload" label={t("hero.cta")} />
          <button className="glass rounded-full px-6 py-3 text-sm font-semibold text-ink/80">
            Watch Demo
          </button>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.1 }}
        className="glass neu grid gap-6 rounded-3xl p-8 md:grid-cols-3"
      >
        {[
          t("features.speed"),
          t("features.explain"),
          t("features.secure")
        ].map((item) => (
          <div key={item} className="flex flex-col gap-2">
            <span className="text-sm uppercase tracking-[0.2em] text-ink/60">Feature</span>
            <span className="text-lg font-semibold text-ink">{item}</span>
            <span className="text-sm text-ink/60">
              Enterprise-grade AI checks with evidence-grade outputs.
            </span>
          </div>
        ))}
      </motion.div>
    </section>
  );
}
