"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { getToken } from "@/lib/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/auth");
    }
  }, [router]);

  return (
    <main className="min-h-screen px-6 py-8 md:px-12">
      <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
        <Sidebar />
        <section className="space-y-8">{children}</section>
      </div>
    </main>
  );
}
