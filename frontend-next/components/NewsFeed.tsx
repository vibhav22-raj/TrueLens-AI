"use client";

import { motion } from "framer-motion";
import { ShieldAlert, Video, Newspaper } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function NewsFeed() {
  const { t } = useTranslation();
  const items = [
    {
      title: t("dashboard.news.items.0.title"),
      summary: t("dashboard.news.items.0.summary"),
      icon: ShieldAlert,
      tag: t("dashboard.news.items.0.tag")
    },
    {
      title: t("dashboard.news.items.1.title"),
      summary: t("dashboard.news.items.1.summary"),
      icon: Video,
      tag: t("dashboard.news.items.1.tag")
    },
    {
      title: t("dashboard.news.items.2.title"),
      summary: t("dashboard.news.items.2.summary"),
      icon: Newspaper,
      tag: t("dashboard.news.items.2.tag")
    },
    {
      title: t("dashboard.news.items.3.title"),
      summary: t("dashboard.news.items.3.summary"),
      icon: ShieldAlert,
      tag: t("dashboard.news.items.3.tag")
    }
  ];

  return (
    <div className="glass rounded-[26px] border border-white/10 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">{t("dashboard.news.title")}</h2>
        <span className="rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-rose-200">
          {t("dashboard.news.live")}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {items.map((item, index) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-white/10 p-2 text-rose-200">
                <item.icon size={16} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-white/40">{item.tag}</p>
                <h3 className="text-sm font-semibold text-white">{item.title}</h3>
              </div>
            </div>
            <p className="mt-2 text-xs text-white/60">{item.summary}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
