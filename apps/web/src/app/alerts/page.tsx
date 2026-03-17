"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch } from "@/lib/api";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [status, setStatus] = useState<string>("");

  async function refresh() {
    const qs = new URLSearchParams();
    qs.set("limit", "500");
    if (status) qs.set("status_filter", status);
    const a = await apiFetch<Alert[]>(`/alerts?${qs.toString()}`);
    setAlerts(a);
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, [status]);

  async function ack(id: string) {
    await apiFetch(`/alerts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "acked" })
    });
    await refresh();
  }

  return (
    <RequireAuth>
      <Card
        title="Alerts"
        right={
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-xs text-white/85 outline-none"
          >
            <option value="">All</option>
            <option value="open">open</option>
            <option value="acked">acked</option>
            <option value="closed">closed</option>
          </select>
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
              {alerts.map((a) => (
                <tr key={a.id} className="border-t border-[var(--stroke)]">
                  <td className="py-2">
                    <div className="font-medium">{a.title}</div>
                    <div className="text-xs text-white/60 line-clamp-2">{a.description}</div>
                  </td>
                  <td className="py-2 font-mono text-xs text-white/75">{a.severity}</td>
                  <td className="py-2 font-mono text-xs text-white/75">{a.status}</td>
                  <td className="py-2 text-xs text-white/55">{new Date(a.updated_at).toLocaleString()}</td>
                  <td className="py-2">
                    {a.status === "open" ? (
                      <button
                        onClick={() => ack(a.id)}
                        className="rounded-xl border border-neon-400/30 bg-neon-500/15 px-3 py-1 text-xs text-neon-300 hover:bg-neon-500/25"
                      >
                        Ack
                      </button>
                    ) : (
                      <span className="text-xs text-white/45">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {alerts.length === 0 ? <div className="mt-3 text-sm text-white/65">No alerts.</div> : null}
        </div>
      </Card>
    </RequireAuth>
  );
}

