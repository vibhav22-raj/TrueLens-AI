import { ReactNode } from "react";

export default function StatCard({
  title,
  value,
  helper,
  icon
}: {
  title: string;
  value: string;
  helper: string;
  icon?: ReactNode;
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-ink/60">{title}</p>
        {icon}
      </div>
      <p className="mt-3 text-2xl font-semibold">{value}</p>
      <p className="mt-2 text-xs text-ink/60">{helper}</p>
    </div>
  );
}
