"use client";

import { useEffect, useState } from "react";
import ResultsPanel from "@/components/ResultsPanel";
import { apiHistory } from "@/lib/api";

interface ResultData {
  verdict: string;
  confidence: number;
  raw_score: number;
  heatmap_url?: string | null;
  filename?: string;
}

export default function ResultsPage() {
  const [result, setResult] = useState<ResultData | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem("ds_last_result");
    if (stored) {
      setResult(JSON.parse(stored));
      return;
    }

    apiHistory()
      .then((history) => {
        if (history?.[0]) {
          setResult({
            filename: history[0].filename,
            verdict: history[0].prediction.verdict,
            confidence: history[0].prediction.confidence,
            raw_score: history[0].prediction.raw_score,
            heatmap_url: history[0].prediction.heatmap_url
          });
        }
      })
      .catch(() => null);
  }, []);

  if (!result) {
    return (
      <div className="glass rounded-3xl p-8">
        <h1 className="text-2xl font-semibold">Results</h1>
        <p className="mt-2 text-sm text-ink/60">No recent detection found. Upload media first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="glass rounded-3xl p-8">
        <h1 className="text-2xl font-semibold">Results</h1>
        <p className="mt-2 text-sm text-ink/60">File: {result.filename}</p>
      </div>
      <ResultsPanel
        verdict={result.verdict}
        confidence={result.confidence}
        rawScore={result.raw_score}
        heatmapUrl={result.heatmap_url}
      />
    </div>
  );
}
