"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch } from "@/lib/api";
import type { Role, User } from "@/lib/types";

export default function SettingsPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setUsers(await apiFetch<User[]>("/users"));
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function createUser(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await apiFetch<User>("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role })
      });
      setEmail("");
      setPassword("");
      setRole("viewer");
      await refresh();
    } catch (err: any) {
      setError(err?.message ?? "Failed to create user");
    }
  }

  return (
    <RequireAuth roles={["admin"]}>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card title="Users (Admin)">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-white/60">
                  <tr>
                    <th className="py-2">Email</th>
                    <th className="py-2">Role</th>
                    <th className="py-2">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-t border-[var(--stroke)]">
                      <td className="py-2">{u.email}</td>
                      <td className="py-2 font-mono text-xs text-white/75">{u.role}</td>
                      <td className="py-2 font-mono text-xs text-white/75">{String(u.is_active)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 ? <div className="mt-3 text-sm text-white/65">No users.</div> : null}
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Create User">
            <form className="space-y-3" onSubmit={createUser}>
              <label className="block">
                <div className="text-xs text-white/60">Email</div>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="analyst@example.com"
                />
              </label>
              <label className="block">
                <div className="text-xs text-white/60">Password</div>
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="min 8 chars"
                />
              </label>
              <label className="block">
                <div className="text-xs text-white/60">Role</div>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-sm text-white/85 outline-none"
                >
                  <option value="viewer">viewer</option>
                  <option value="analyst">analyst</option>
                  <option value="admin">admin</option>
                </select>
              </label>

              {error ? (
                <div className="rounded-xl border border-ember-400/30 bg-ember-500/10 px-3 py-2 text-sm text-ember-300">
                  {error}
                </div>
              ) : null}

              <button className="w-full rounded-xl bg-neon-500 px-3 py-2 text-sm font-semibold text-black hover:bg-neon-400">
                Create
              </button>
            </form>
          </Card>
        </div>
      </div>
    </RequireAuth>
  );
}

