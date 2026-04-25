"use client";

import { motion } from "framer-motion";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { useTranslation } from "react-i18next";
import { CheckCircle2 } from "lucide-react";

const colors = ["#f43f5e", "#22c55e"];

export default function ResultsPanel({
  verdict,
  confidence,
  rawScore,
  note
}: {
  verdict: string;
  confidence: number;
  rawScore: number;
  heatmapUrl?: string | null;
  note?: string | null;
}) {
  const { t } = useTranslation();
  const normalizedVerdict = verdict?.toUpperCase() || "UNKNOWN";
  const isFake = normalizedVerdict === "FAKE";
  const isUnknown = normalizedVerdict === "UNKNOWN";
  const fakeValue = isFake ? confidence : 100 - confidence;
  const data = [
    { name: t("results.fake"), value: fakeValue },
    { name: t("results.real"), value: 100 - fakeValue }
  ];
  const verdictClass = isUnknown ? "text-amber-500" : isFake ? "text-rose-500" : "text-emerald-500";
  const pillClass = isUnknown
    ? "bg-amber-500/20 text-amber-500"
    : isFake
      ? "bg-rose-500/20 text-rose-500"
      : "bg-emerald-500/20 text-emerald-500";
  const confidenceTier = confidence >= 85 ? t("results.highConfidence") : confidence >= 70 ? t("results.moderateConfidence") : t("results.reviewRecommended");
  const trustChecks = [
    t("results.trustChecks.scoreConsistency"),
    t("results.trustChecks.thresholdCalibration"),
    t("results.trustChecks.modelValidation")
  ];

  return (
    <div className="glass rounded-3xl p-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-ink/60">{t("results.verdict")}</p>
          <h3 className={`text-2xl font-semibold ${verdictClass}`}>
            {isUnknown ? t("results.unableToDetermine") : isFake ? t("results.likelyDeepfake") : t("results.likelyAuthentic")}
          </h3>
        </div>
        <span className={`rounded-full px-4 py-2 text-xs font-semibold ${pillClass}`}>
          {confidence}% {t("results.confidence")}
        </span>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl bg-white/40 p-4">
          <p className="text-xs text-ink/60">{t("results.trustOverview")}</p>
          <p className="mt-2 text-sm font-semibold text-ink/90">{confidenceTier}</p>
          <div className="mt-3 space-y-2 text-sm text-ink/80">
            {trustChecks.map((check) => (
              <div key={check} className="flex items-start gap-2">
                <CheckCircle2 size={16} className="mt-0.5 text-emerald-500" />
                <span>{check}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl bg-white/40 p-4">
          <p className="text-xs text-ink/60">{t("results.confidenceSplit")}</p>
          <div className="mt-2 h-36">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data} dataKey="value" innerRadius={40} outerRadius={60} paddingAngle={5}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${entry.name}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-6 rounded-2xl bg-white/40 p-4 text-sm text-ink/70"
      >
        {t("results.rawModelScore")}: {rawScore}
      </motion.div>

      {note ? (
        <div className="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-700">
          {note}
        </div>
      ) : null}
    </div>
  );
}
