"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud } from "lucide-react";
import { useTranslation } from "react-i18next";

interface UploadBoxProps {
  mode: "image" | "video";
  file: File | null;
  loading: boolean;
  result: {
    verdict: string;
    confidence: number;
    rawScore?: number;
    heatmapUrl?: string | null;
    note?: string | null;
  } | null;
  onFile: (file: File) => void;
}

export default function UploadBox({ mode, file, loading, result, onFile }: UploadBoxProps) {
  const { t } = useTranslation();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const accept = useMemo(() => (mode === "image" ? "image/*" : "video/*"), [mode]);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleIncomingFile = (incoming?: File) => {
    if (!incoming) return;
    if (mode === "image" && !incoming.type.startsWith("image/")) return;
    if (mode === "video" && !incoming.type.startsWith("video/")) return;
    onFile(incoming);
  };

  return (
    <div className="mt-6 space-y-6">
      <label
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          handleIncomingFile(event.dataTransfer.files?.[0]);
        }}
        className={`flex cursor-pointer flex-col items-center gap-4 rounded-3xl border border-dashed px-8 py-10 text-center transition ${
          dragging
            ? "border-rose-300 bg-rose-500/10"
            : "border-white/20 bg-white/5"
        }`}
      >
        <UploadCloud className="text-rose-200" />
        <div>
          <p className="text-sm font-semibold text-white">{t("dashboard.uploadBox.dragDrop", { mode })}</p>
          <p className="text-xs text-white/60">{t("dashboard.uploadBox.supportedFiles")}</p>
        </div>
        <input
          type="file"
          className="hidden"
          accept={accept}
          onChange={(event) => {
            const selected = event.target.files?.[0];
            handleIncomingFile(selected);
          }}
        />
      </label>

      {previewUrl && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <p className="mb-3 text-xs text-white/60">{t("dashboard.uploadBox.selected", { filename: file?.name })}</p>
          {mode === "image" ? (
            <img src={previewUrl} alt="Preview" className="w-full rounded-3xl object-cover" />
          ) : (
            <video src={previewUrl} controls className="w-full rounded-3xl" />
          )}
        </motion.div>
      )}

      <div className="rounded-3xl border border-white/10 bg-white/5 px-6 py-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-white">{t("dashboard.uploadBox.scanResult")}</p>
          {loading && (
            <span className="flex items-center gap-2 text-xs text-white/60">
              <span className="h-3 w-3 animate-spin rounded-full border border-rose-200 border-t-transparent" />
              {t("dashboard.uploadBox.scanning")}
            </span>
          )}
        </div>

        {result ? (
          <div className="mt-4 flex items-center justify-between">
            <div>
              <p
                className={`text-lg font-semibold ${
                  result.verdict === "UNKNOWN"
                    ? "text-amber-300"
                    : result.verdict === "FAKE"
                      ? "text-rose-300"
                      : "text-emerald-300"
                }`}
              >
                {result.verdict}
              </p>
              <p className="text-xs text-white/60">{t("dashboard.uploadBox.confidence")}</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-semibold text-white">{result.confidence.toFixed(1)}%</p>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-xs text-white/60">{t("dashboard.uploadBox.emptyState")}</p>
        )}
      </div>
    </div>
  );
}
