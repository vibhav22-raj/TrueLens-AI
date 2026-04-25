"use client";

import { useEffect, useState } from "react";
import { apiAdminAnalytics } from "@/lib/api";
import { BarChart, Bar, XAxis, ResponsiveContainer } from "recharts";

export default function AdminAnalytics() {
  const [data, setData] = useState<{ users: number; uploads: number; predictions: number } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiAdminAnalytics()
      .then(setData)
      .catch(() => setError("Admin access required."));
  }, []);

  if (error) {
    return <div className="glass rounded-2xl p-6 text-sm text-rose-500">{error}</div>;
  }

  if (!data) {
    return <div className="glass rounded-2xl p-6 text-sm text-ink/60">Loading analytics...</div>;
  }

  const chartData = [
    { name: "Users", value: data.users },
    { name: "Uploads", value: data.uploads },
    { name: "Predictions", value: data.predictions }
  ];

  return (
    <div className="glass rounded-3xl p-8">
      <h2 className="text-lg font-semibold">Platform Analytics</h2>
      <div className="mt-4 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="#94a3b8" />
            <Bar dataKey="value" fill="#6366f1" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
