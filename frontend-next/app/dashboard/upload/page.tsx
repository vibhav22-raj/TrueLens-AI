"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import UploadDropzone from "@/components/UploadDropzone";
import Toast from "@/components/Toast";
import { apiPredict, extractApiError } from "@/lib/api";

export default function UploadPage() {
  const [toast, setToast] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const router = useRouter();

  const handleFile = async (file: File) => {
    setPreview(URL.createObjectURL(file));
    try {
      const result = await apiPredict(file);
      const confidenceValue = Number(result?.confidence_percent ?? result?.confidence ?? 0);
      const normalizedConfidence = confidenceValue > 1 ? confidenceValue : confidenceValue * 100;

      window.localStorage.setItem(
        "ds_last_result",
        JSON.stringify({
          filename: file.name,
          verdict: result?.result ?? result?.verdict ?? "UNKNOWN",
          confidence: Number(normalizedConfidence.toFixed(2)),
          raw_score: Number(result?.raw_score ?? 0),
          heatmap_url: result?.heatmap_url ?? null,
          note: result?.note ?? null
        })
      );

      setToast("Detection completed. Redirecting...");
      setTimeout(() => router.push("/dashboard/results"), 800);
    } catch (err) {
      setToast(extractApiError(err, "Detection failed. Please try again."));
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass rounded-3xl p-8">
        <h1 className="text-2xl font-semibold">Upload for Detection</h1>
        <p className="mt-2 text-sm text-ink/60">Drag media, watch AI process it live.</p>
      </div>
      <UploadDropzone onFile={handleFile} />
      {preview && (
        <div className="glass rounded-2xl p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/60">Preview</p>
          <img src={preview} alt="preview" className="mt-3 max-h-64 w-full rounded-2xl object-cover" />
        </div>
      )}
      {toast && <Toast message={toast} />}
    </div>
  );
}
