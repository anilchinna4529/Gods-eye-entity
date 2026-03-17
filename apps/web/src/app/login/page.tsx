"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiFetch<User>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      router.replace("/");
    } catch (err: any) {
      setError(err?.message ?? "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--card)] p-6 backdrop-blur">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <p className="mt-1 text-sm text-white/65">
          Use the bootstrap admin credentials from your <span className="font-mono">.env</span>.
        </p>

        <form className="mt-6 space-y-3" onSubmit={onSubmit}>
          <label className="block">
            <div className="text-xs text-white/60">Email</div>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
              placeholder="admin@example.com"
              autoComplete="username"
            />
          </label>

          <label className="block">
            <div className="text-xs text-white/60">Password</div>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
              placeholder="••••••••"
              type="password"
              autoComplete="current-password"
            />
          </label>

          {error ? (
            <div className="rounded-xl border border-ember-400/30 bg-ember-500/10 px-3 py-2 text-sm text-ember-300">
              {error}
            </div>
          ) : null}

          <button
            disabled={busy}
            className="w-full rounded-xl bg-neon-500 px-3 py-2 text-sm font-semibold text-black hover:bg-neon-400 disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

