"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch } from "@/lib/api";
import type { Finding } from "@/lib/types";

const severities = ["critical", "high", "medium", "low", "info"];
const statuses = ["open", "triaged", "mitigated", "false_positive"];

export default function FindingsPage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [status, setStatus] = useState<string>("");
  const [severity, setSeverity] = useState<string>("");

  async function refresh() {
    const qs = new URLSearchParams();
    qs.set("limit", "500");
    if (status) qs.set("status_filter", status);
    if (severity) qs.set("severity", severity);
    const f = await apiFetch<Finding[]>(`/findings?${qs.toString()}`);
    setFindings(f);
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, [status, severity]);

  async function setFindingStatus(id: string, next: string) {
    await apiFetch(`/findings/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: next })
    });
    await refresh();
  }

  return (
    <RequireAuth>
      <div className="space-y-5">
        <Card
          title="Findings"
          right={
            <div className="flex gap-2">
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-xs text-white/85 outline-none"
              >
                <option value="">All statuses</option>
                {statuses.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-xs text-white/85 outline-none"
              >
                <option value="">All severities</option>
                {severities.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-white/60">
                <tr>
                  <th className="py-2">Title</th>
                  <th className="py-2">Severity</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Updated</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f) => (
                  <tr key={f.id} className="border-t border-[var(--stroke)]">
                    <td className="py-2">
                      <div className="font-medium">{f.title}</div>
                      <div className="text-xs text-white/60 line-clamp-2">{f.description}</div>
                    </td>
                    <td className="py-2 font-mono text-xs text-white/75">{f.severity}</td>
                    <td className="py-2 font-mono text-xs text-white/75">{f.status}</td>
                    <td className="py-2 text-xs text-white/55">{new Date(f.updated_at).toLocaleString()}</td>
                    <td className="py-2">
                      <select
                        value={f.status}
                        onChange={(e) => setFindingStatus(f.id, e.target.value)}
                        className="rounded-xl border border-[var(--stroke)] bg-black/25 px-2 py-1 text-xs text-white/85 outline-none"
                      >
                        {statuses.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {findings.length === 0 ? <div className="mt-3 text-sm text-white/65">No findings.</div> : null}
          </div>
        </Card>
      </div>
    </RequireAuth>
  );
}

