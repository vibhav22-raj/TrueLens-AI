"use client";

import { useEffect, useState } from "react";
import HistoryCard from "@/components/HistoryCard";
import { apiHistory } from "@/lib/api";
import LoadingSkeleton from "@/components/LoadingSkeleton";

interface HistoryItem {
  id: number;
  filename: string;
  media_type: string;
  created_at: string | null;
  prediction: {
    verdict: string;
    confidence: number;
  };
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiHistory()
      .then((data) => setItems(data))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="glass rounded-3xl p-8">
        <h1 className="text-2xl font-semibold">History</h1>
        <p className="mt-2 text-sm text-ink/60">Your latest detections, ready to audit.</p>
      </div>
      {loading && (
        <div className="grid gap-4 md:grid-cols-3">
          <LoadingSkeleton />
          <LoadingSkeleton />
          <LoadingSkeleton />
        </div>
      )}
      {!loading && (
        <div className="grid gap-4 md:grid-cols-3">
          {items.length === 0 && (
            <div className="glass rounded-2xl p-5 text-sm text-ink/60">
              No history yet. Upload media to generate results.
            </div>
          )}
          {items.map((item) => (
            <HistoryCard
              key={item.id}
              title={item.filename}
              status={`${item.prediction.verdict} (${item.prediction.confidence}%)`}
              date={item.created_at ? new Date(item.created_at).toLocaleDateString() : ""}
            />
          ))}
        </div>
      )}
    </div>
  );
}
