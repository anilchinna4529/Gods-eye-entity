"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Role } from "@/lib/types";
import { useMe } from "@/lib/auth";

export function RequireAuth({
  children,
  roles
}: {
  children: React.ReactNode;
  roles?: Role[];
}) {
  const router = useRouter();
  const { user, loading } = useMe();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--card)] p-6">
        Loading…
      </div>
    );
  }
  if (!user) return null;

  if (roles && !roles.includes(user.role)) {
    return (
      <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--card)] p-6">
        Forbidden for role <span className="font-mono">{user.role}</span>.
      </div>
    );
  }

  return <>{children}</>;
}

