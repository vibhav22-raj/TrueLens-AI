"use client";

import { useEffect, useState } from "react";
import ProfileCard from "@/components/ProfileCard";
import { apiMe } from "@/lib/api";

export default function ProfilePage() {
  const [user, setUser] = useState<{ name: string; email: string; role: string } | null>(null);

  useEffect(() => {
    apiMe().then(setUser).catch(() => setUser(null));
  }, []);

  return (
    <div className="space-y-6">
      <div className="glass rounded-3xl p-8">
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="mt-2 text-sm text-ink/60">Manage account settings and roles.</p>
      </div>
      {user ? (
        <div className="glass rounded-3xl p-8">
          <p className="text-lg font-semibold">{user.name}</p>
          <p className="text-sm text-ink/60">{user.email}</p>
          <p className="mt-4 text-sm text-ink/60">Role: {user.role}</p>
        </div>
      ) : (
        <ProfileCard />
      )}
    </div>
  );
}
