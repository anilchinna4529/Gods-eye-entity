"use client";

import { useEffect, useMemo, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch, WS_BASE } from "@/lib/api";
import type { Alert, Asset, EventMessage, Execution, Finding } from "@/lib/types";

function Pill({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 rounded-xl border border-[var(--stroke)] bg-black/20 px-4 py-3">
      <div className="text-xs text-white/60">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}

export default function OverviewPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [events, setEvents] = useState<EventMessage[]>([]);

  const openAlerts = useMemo(() => alerts.filter((a) => a.status === "open").length, [alerts]);
  const openFindings = useMemo(() => findings.filter((f) => f.status === "open").length, [findings]);
  const running = useMemo(() => executions.filter((e) => e.status === "running" || e.status === "queued").length, [executions]);

  useEffect(() => {
    let alive = true;
    Promise.all([
      apiFetch<Asset[]>("/assets?limit=200"),
      apiFetch<Alert[]>("/alerts?limit=200"),
      apiFetch<Finding[]>("/findings?limit=200"),
      apiFetch<Execution[]>("/executions?limit=200")
    ])
      .then(([a, al, f, ex]) => {
        if (!alive) return;
        setAssets(a);
        setAlerts(al);
        setFindings(f);
        setExecutions(ex);
      })
      .catch(() => {
        // ignore; auth wrapper handles redirect
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/events`);
    ws.onmessage = (msg) => {
      try {
        const ev = JSON.parse(msg.data) as EventMessage;
        setEvents((prev) => [ev, ...prev].slice(0, 30));
        if (ev.type === "execution.updated") {
          apiFetch<Execution[]>("/executions?limit=200").then(setExecutions).catch(() => undefined);
        }
        if (ev.type?.startsWith("alert.")) {
          apiFetch<Alert[]>("/alerts?limit=200").then(setAlerts).catch(() => undefined);
        }
        if (ev.type?.startsWith("finding.")) {
          apiFetch<Finding[]>("/findings?limit=200").then(setFindings).catch(() => undefined);
        }
        if (ev.type?.startsWith("asset.")) {
          apiFetch<Asset[]>("/assets?limit=200").then(setAssets).catch(() => undefined);
        }
      } catch {
        // ignore
      }
    };
    return () => ws.close();
  }, []);

  return (
    <RequireAuth>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-5">
          <Card title="At A Glance">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Pill label="Assets" value={`${assets.length}`} />
              <Pill label="Open Alerts" value={`${openAlerts}`} />
              <Pill label="Open Findings" value={`${openFindings}`} />
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Pill label="Queued/Running Executions" value={`${running}`} />
              <Pill label="Defensive Actions" value="Allowlisted" />
              <Pill label="Audit Trail" value="Enabled" />
            </div>
          </Card>

          <Card title="Live Event Stream">
            <div className="space-y-2">
              {events.length === 0 ? (
                <div className="text-sm text-white/65">Waiting for events…</div>
              ) : (
                events.map((ev, i) => (
                  <div key={i} className="rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2">
                    <div className="text-xs text-white/70">{ev.type}</div>
                    <pre className="mt-1 overflow-x-auto text-xs text-white/60">
                      {JSON.stringify(ev.data ?? {}, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Notes">
            <div className="text-sm text-white/70 space-y-2">
              <p>
                This v1 build is defensive-only. High-impact automations can be gated by playbook approval.
              </p>
              <p>
                Use <span className="font-mono">Playbooks</span> and <span className="font-mono">Executions</span> to run allowlisted actions like
                importing assets, ingesting threat intel, and scanning uploaded artifacts for exposed secrets.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </RequireAuth>
  );
}

