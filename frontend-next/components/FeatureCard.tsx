import { ReactNode } from "react";

export default function FeatureCard({
  title,
  description,
  icon
}: {
  title: string;
  description: string;
  icon: ReactNode;
}) {
  return (
    <div className="glass rounded-2xl p-6 transition hover:-translate-y-1 hover:shadow-soft">
      <div className="mb-4 text-ink">{icon}</div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-ink/60">{description}</p>
    </div>
  );
}
