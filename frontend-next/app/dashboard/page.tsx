"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import dynamic from "next/dynamic";
import { useTranslation } from "react-i18next";
import { Activity, ShieldCheck, Sparkles } from "lucide-react";
import AnimatedBackground from "@/components/AnimatedBackground";
import Navbar from "@/components/Navbar";
import LanguageSelector from "@/components/LanguageSelector";
import Toast from "@/components/Toast";
import { apiPredict, extractApiError } from "@/lib/api";
import { clearToken } from "@/lib/auth";

type PredictionResult = {
  verdict: string;
  confidence: number;
  rawScore: number;
  heatmapUrl?: string | null;
  note?: string | null;
};

const sectionVariants = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.45,
      ease: "easeOut"
    }
  }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.09,
      delayChildren: 0.06
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } }
};

const UploadBox = dynamic(() => import("@/components/UploadBox"), {
  ssr: false,
  loading: () => (
    <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 px-8 py-16 text-center text-sm text-white/60">
      Loading uploader...
    </div>
  )
});

const ResultsPanel = dynamic(() => import("@/components/ResultsPanel"), {
  ssr: false,
  loading: () => (
    <div className="glass rounded-[30px] border border-white/10 p-6">
      <p className="text-sm text-white/70">Loading result panel...</p>
    </div>
  )
});

export default function DashboardPage() {
  const [mode, setMode] = useState<"image" | "video" | null>("image");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const router = useRouter();
  const { t } = useTranslation();

  const trustStatements = useMemo(
    () => [
      t("dashboard.trustSignals.items.ai"),
      t("dashboard.trustSignals.items.trusted"),
      t("dashboard.trustSignals.items.protect")
    ],
    [t]
  );

  const currentVerdict = result?.verdict ?? "PENDING";
  const currentConfidence = result?.confidence ? `${result.confidence.toFixed(1)}%` : "--";

  const handleFile = async (uploaded: File) => {
    setFile(uploaded);
    setResult(null);
    setLoading(true);

    try {
      const data = await apiPredict(uploaded);
      const verdict = String(data?.result ?? data?.verdict ?? data?.label ?? "UNKNOWN").toUpperCase();

      const confidenceValue = Number(data?.confidence_percent ?? data?.confidence ?? data?.score ?? 0);
      const normalizedConfidence = confidenceValue > 1 ? confidenceValue : confidenceValue * 100;

      const normalizedResult = {
        verdict,
        confidence: Number.isFinite(normalizedConfidence) ? Number(normalizedConfidence.toFixed(2)) : 0,
        rawScore: Number(data?.raw_score ?? data?.rawScore ?? data?.probability ?? 0),
        heatmapUrl: data?.heatmap_url ?? data?.heatmapUrl ?? null,
        note: data?.note ?? null
      };

      setResult(normalizedResult);
      window.localStorage.setItem(
        "ds_last_result",
        JSON.stringify({
          filename: uploaded.name,
          verdict: normalizedResult.verdict,
          confidence: normalizedResult.confidence,
          raw_score: normalizedResult.rawScore,
          heatmap_url: normalizedResult.heatmapUrl,
          note: normalizedResult.note
        })
      );

      setToast(data?.note ? data.note : t("dashboard.toasts.predictionComplete"));
    } catch (err) {
      setToast(extractApiError(err, t("dashboard.toasts.predictionFailed")));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden">
      <AnimatedBackground />
      <Navbar variant="dashboard" />

      <div className="fixed right-4 top-28 z-30 md:right-10 md:top-32">
        <LanguageSelector />
      </div>

      <section className="relative z-10 mx-auto w-full max-w-7xl px-6 pb-24 pt-12">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={sectionVariants}
          className="glass relative overflow-hidden rounded-[32px] border border-white/10 p-7 md:p-10"
        >
          <motion.div
            className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-300/80 to-transparent"
            initial={{ x: "-30%", opacity: 0.2 }}
            animate={{ x: "30%", opacity: 0.9 }}
            transition={{ duration: 3.2, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
          />
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-rose-500/20 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 left-1/3 h-56 w-56 rounded-full bg-cyan-400/20 blur-3xl" />

          <div className="relative flex flex-col gap-6">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-white/55">{t("dashboard.brand")}</p>
              <h1 className="mt-3 text-3xl font-semibold text-white md:text-4xl">{t("dashboard.page.title")}</h1>
              <p className="mt-3 max-w-3xl text-sm text-white/70 md:text-base">{t("dashboard.page.subtitle")}</p>
            </div>

            <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid gap-4 md:grid-cols-3">
              <motion.div
                variants={itemVariants}
                whileHover={{ y: -4, scale: 1.01 }}
                className="rounded-2xl border border-white/15 bg-black/20 px-5 py-4 shadow-[0_16px_40px_rgba(8,10,20,0.2)]"
              >
                <p className="text-[11px] uppercase tracking-[0.2em] text-white/50">System Status</p>
                <p className="mt-2 flex items-center gap-2 text-base font-semibold text-emerald-300">
                  <Activity size={16} /> Online
                </p>
              </motion.div>

              <motion.div
                variants={itemVariants}
                whileHover={{ y: -4, scale: 1.01 }}
                className="rounded-2xl border border-white/15 bg-black/20 px-5 py-4 shadow-[0_16px_40px_rgba(8,10,20,0.2)]"
              >
                <p className="text-[11px] uppercase tracking-[0.2em] text-white/50">Last Verdict</p>
                <p className="mt-2 flex items-center gap-2 text-base font-semibold text-white">
                  <ShieldCheck size={16} /> {currentVerdict}
                </p>
              </motion.div>

              <motion.div
                variants={itemVariants}
                whileHover={{ y: -4, scale: 1.01 }}
                className="rounded-2xl border border-white/15 bg-black/20 px-5 py-4 shadow-[0_16px_40px_rgba(8,10,20,0.2)]"
              >
                <p className="text-[11px] uppercase tracking-[0.2em] text-white/50">Confidence</p>
                <p className="mt-2 flex items-center gap-2 text-base font-semibold text-white">
                  <Sparkles size={16} /> {currentConfidence}
                </p>
              </motion.div>
            </motion.div>
          </div>
        </motion.div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mt-8 grid gap-8 xl:grid-cols-[1.7fr_1fr]"
        >
          <motion.div
            variants={itemVariants}
            whileHover={{ y: -2 }}
            className="glass rounded-[30px] border border-white/10 p-6 md:p-8 shadow-[0_30px_60px_rgba(7,10,25,0.28)]"
          >
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-5">
              <div>
                <h2 className="text-xl font-semibold text-white">{t("dashboard.mediaVerification.title")}</h2>
                <p className="mt-2 text-sm text-white/65">{t("dashboard.mediaVerification.subtitle")}</p>
              </div>

              <div className="flex rounded-full border border-white/15 bg-white/5 p-1">
                <button
                  onClick={() => {
                    setMode("image");
                    setFile(null);
                    setResult(null);
                  }}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                    mode === "image" ? "bg-white text-black" : "text-white/70"
                  }`}
                >
                  {t("dashboard.mediaVerification.uploadImage")}
                </button>
                <button
                  onClick={() => {
                    setMode("video");
                    setFile(null);
                    setResult(null);
                  }}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                    mode === "video" ? "bg-white text-black" : "text-white/70"
                  }`}
                >
                  {t("dashboard.mediaVerification.uploadVideo")}
                </button>
              </div>
            </div>

            {mode ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <UploadBox mode={mode} file={file} loading={loading} result={result} onFile={handleFile} />
              </motion.div>
            ) : (
              <div className="mt-8 rounded-3xl border border-dashed border-white/15 bg-white/5 px-8 py-16 text-center text-sm text-white/60">
                {t("dashboard.mediaVerification.selectMode")}
              </div>
            )}
          </motion.div>

          <motion.div variants={itemVariants} className="flex flex-col gap-6">
            {result ? (
              <ResultsPanel
                verdict={result.verdict}
                confidence={Number(result.confidence.toFixed(1))}
                rawScore={result.rawScore}
                heatmapUrl={result.heatmapUrl}
                note={result.note}
              />
            ) : (
              <motion.div
                whileHover={{ y: -2 }}
                className="glass rounded-[30px] border border-white/10 p-6 shadow-[0_24px_50px_rgba(7,10,25,0.22)]"
              >
                <p className="text-xs uppercase tracking-[0.2em] text-white/45">Ready to Analyze</p>
                <h3 className="mt-2 text-lg font-semibold text-white">Upload media to generate report</h3>
                <p className="mt-2 text-sm text-white/65">Your verdict, confidence profile, and trust summary will appear here.</p>
              </motion.div>
            )}

            <motion.div
              whileHover={{ y: -2 }}
              className="glass rounded-[30px] border border-white/10 p-6 shadow-[0_24px_50px_rgba(7,10,25,0.2)]"
            >
              <h3 className="text-base font-semibold text-white">{t("dashboard.trustSignals.title")}</h3>
              <div className="mt-4 grid gap-3 text-sm text-white/75">
                {trustStatements.map((item) => (
                  <motion.div
                    key={item}
                    whileHover={{ x: 3 }}
                    className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                  >
                    {item}
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              whileHover={{ y: -2 }}
              className="glass rounded-[30px] border border-white/10 p-6 shadow-[0_24px_50px_rgba(7,10,25,0.2)]"
            >
              <h3 className="text-base font-semibold text-white">{t("dashboard.modelDecision.title")}</h3>
              <p className="mt-2 text-sm text-white/65">{t("dashboard.modelDecision.subtitle")}</p>
              <div className="mt-4 grid gap-3 text-sm text-white/75">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">{t("dashboard.modelDecision.items.faceBoundary")}</div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">{t("dashboard.modelDecision.items.texture")}</div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">{t("dashboard.modelDecision.items.lighting")}</div>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      </section>

      <button
        onClick={() => {
          clearToken();
          router.push("/auth");
        }}
        className="glass fixed bottom-6 right-6 z-20 rounded-full border border-rose-500/40 bg-rose-500/10 px-5 py-3 text-xs font-semibold text-rose-100 shadow-[0_0_25px_rgba(244,63,94,0.35)]"
      >
        {t("dashboard.logout")}
      </button>

      {toast && <Toast message={toast} />}
    </main>
  );
}
