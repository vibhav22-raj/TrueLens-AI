import StatCard from "@/components/StatCard";
import AdminAnalytics from "@/components/AdminAnalytics";
import { Users, UploadCloud, ShieldCheck } from "lucide-react";

export default function AdminPage() {
  return (
    <main className="min-h-screen px-6 py-10 md:px-12">
      <div className="glass rounded-3xl p-8">
        <h1 className="text-3xl font-semibold">Admin Analytics</h1>
        <p className="mt-2 text-sm text-ink/60">Overview of platform usage and alerts.</p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <StatCard title="Active Users" value="Live" helper="Real-time count" icon={<Users size={18} />} />
        <StatCard title="Uploads" value="Live" helper="Last 30 days" icon={<UploadCloud size={18} />} />
        <StatCard title="Critical Alerts" value="Live" helper="Needs review" icon={<ShieldCheck size={18} />} />
      </div>

      <div className="mt-6">
        <AdminAnalytics />
      </div>
    </main>
  );
}
