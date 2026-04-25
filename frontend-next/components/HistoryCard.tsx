export default function HistoryCard({
  title,
  status,
  date
}: {
  title: string;
  status: string;
  date: string;
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-2 text-xs text-ink/60">{date}</p>
      <span className="mt-4 inline-flex rounded-full bg-white/40 px-3 py-1 text-xs font-semibold text-ink/70">
        {status}
      </span>
    </div>
  );
}
