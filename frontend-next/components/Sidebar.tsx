"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, UploadCloud, ShieldCheck, History, UserCircle, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

const links = [
  { href: "/dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { href: "/dashboard/upload", labelKey: "nav.upload", icon: UploadCloud },
  { href: "/dashboard/results", labelKey: "nav.results", icon: ShieldCheck },
  { href: "/dashboard/history", labelKey: "nav.history", icon: History },
  { href: "/dashboard/profile", labelKey: "nav.profile", icon: UserCircle }
];

export default function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();

  return (
    <aside className="glass sticky top-8 h-fit rounded-3xl px-6 py-8">
      <div className="mb-6">
        <p className="text-xs uppercase tracking-[0.3em] text-ink/60">{t("dashboard.sidebar.console")}</p>
        <h2 className="text-xl font-semibold">DeepShield AI</h2>
      </div>
      <nav className="flex flex-col gap-2">
        {links.map(({ href, labelKey, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-colors",
                isActive ? "bg-white text-black shadow-sm" : "text-ink/70 hover:bg-white/15 hover:text-white"
              )}
            >
              <Icon size={16} />
              {t(labelKey)}
            </Link>
          );
        })}
      </nav>
      <div className="mt-8 rounded-2xl bg-white/50 p-4 text-xs text-ink/70">
        <p className="font-semibold">{t("dashboard.sidebar.adminTools")}</p>
        <Link href="/admin" className="mt-2 flex items-center gap-2">
          <Settings size={14} /> {t("dashboard.sidebar.analytics")}
        </Link>
      </div>
    </aside>
  );
}
