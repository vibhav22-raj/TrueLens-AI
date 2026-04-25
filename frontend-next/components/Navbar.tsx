"use client";

import Link from "next/link";

export default function Navbar({ variant = "default" }: { variant?: "default" | "auth" | "dashboard" }) {
  return (
    <nav className="relative z-20 mx-6 mt-6 flex items-center justify-between rounded-full border border-white/10 bg-black/30 px-6 py-3 backdrop-blur-xl md:mx-16">
      <Link href={variant === "auth" ? "/auth" : "/dashboard"} className="text-sm font-semibold text-white">
        DeepShield AI
      </Link>
      <div className="hidden items-center gap-6 text-xs text-white/60 md:flex">
        <span>Secure Media Verification</span>
        <span className="h-1 w-1 rounded-full bg-rose-400/70" />
        <span>Enterprise-grade trust layer</span>
      </div>
      <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] uppercase tracking-[0.3em] text-white/70">
        {variant === "auth" ? "Access" : "Shielded"}
      </div>
    </nav>
  );
}
