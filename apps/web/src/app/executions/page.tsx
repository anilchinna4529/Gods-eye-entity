"use client";

import { useEffect, useMemo, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { API_BASE, apiFetch } from "@/lib/api";
import type { Execution, Playbook, Upload } from "@/lib/types";

type ExecMode = "playbook" | "action";

const actionOptions = [
  { value: "IMPORT_ASSETS", label: "Import Assets (CSV/JSON upload)" },
  { value: "INGEST_INTEL", label: "Ingest Threat Intel (upload)" },
  { value: "CONFIG_SCAN", label: "Config Secret Scan (upload)" },
  { value: "CORRELATE_ALERTS", label: "Correlate Alerts (rules)" }
];

async function uploadFile(file: File): Promise<Upload> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/uploads`, { method: "POST", body: fd, credentials: "include" });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.detail ?? `Upload failed (${res.status})`);
  return body as Upload;
}

export default function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [mode, setMode] = useState<ExecMode>("action");
  const [selectedPlaybookId, setSelectedPlaybookId] = useState<string>("");
  const [action, setAction] = useState(actionOptions[0].value);
  const [upload, setUpload] = useState<Upload | null>(null);
  const [assetId, setAssetId] = useState("");
  const [threshold, setThreshold] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const needsUpload = useMemo(() => ["IMPORT_ASSETS", "INGEST_INTEL", "CONFIG_SCAN"].includes(action), [action]);

  async function refresh() {
    setExecutions(await apiFetch<Execution[]>("/executions?limit=500"));
    setPlaybooks(await apiFetch<Playbook[]>("/playbooks"));
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function onUploadSelected(file: File | null) {
    setError(null);
    setUpload(null);
    if (!file) return;
    try {
      setBusy(true);
      const up = await uploadFile(file);
      setUpload(up);
    } catch (err: any) {
      setError(err?.message ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function createExecution(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "playbook") {
        if (!selectedPlaybookId) throw new Error("Select a playbook.");
        await apiFetch<Execution>("/executions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            execution_type: "playbook",
            playbook_id: selectedPlaybookId,
            params: upload ? { upload_id: upload.id } : {}
          })
        });
      } else {
        const params: Record<string, unknown> = {};
        if (needsUpload) {
          if (!upload) throw new Error("Upload a file for this action.");
          params.upload_id = upload.id;
        }
        if (action === "CONFIG_SCAN" && assetId) params.asset_id = assetId;
        if (action === "CORRELATE_ALERTS") params.threshold = threshold;

        await apiFetch<Execution>("/executions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ execution_type: "action", action, params })
        });
      }
      await refresh();
    } catch (err: any) {
      setError(err?.message ?? "Failed to create execution");
    } finally {
      setBusy(false);
    }
  }

  async function approve(executionId: string) {
    setError(null);
    try {
      await apiFetch(`/executions/${executionId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Approved via UI" })
      });
      await refresh();
    } catch (err: any) {
      setError(err?.message ?? "Approve failed");
    }
  }

  return (
    <RequireAuth>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card title="Executions (Runs)">
            <div className="space-y-2">
              {executions.map((ex) => (
                <div key={ex.id} className="rounded-xl border border-[var(--stroke)] bg-black/20 px-4 py-3">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="text-sm font-medium">
                        {ex.execution_type === "action" ? (
                          <span>Action: {ex.action}</span>
                        ) : (
                          <span>Playbook: {ex.playbook_id}</span>
                        )}
                      </div>
                      <div className="mt-1 text-xs text-white/60">
                        status: <span className="font-mono">{ex.status}</span> · created{" "}
                        {new Date(ex.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {ex.status === "requires_approval" ? (
                        <button
                          onClick={() => approve(ex.id)}
                          className="rounded-xl border border-ember-400/30 bg-ember-500/10 px-3 py-1 text-xs text-ember-300 hover:bg-ember-500/15"
                        >
                          Approve
                        </button>
                      ) : null}
                    </div>
                  </div>

                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs text-white/65">details</summary>
                    <pre className="mt-2 max-h-56 overflow-auto rounded-lg border border-[var(--stroke)] bg-black/30 p-2 text-[11px] text-white/65">
                      {JSON.stringify({ params: ex.params, result: ex.result, log: ex.log }, null, 2)}
                    </pre>
                  </details>
                </div>
              ))}
              {executions.length === 0 ? <div className="text-sm text-white/65">No executions yet.</div> : null}
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Create Execution">
            <form className="space-y-3" onSubmit={createExecution}>
              <label className="block">
                <div className="text-xs text-white/60">Mode</div>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value as ExecMode)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-sm text-white/85 outline-none"
                >
                  <option value="action">Action</option>
                  <option value="playbook">Playbook</option>
                </select>
              </label>

              {mode === "playbook" ? (
                <label className="block">
                  <div className="text-xs text-white/60">Playbook</div>
                  <select
                    value={selectedPlaybookId}
                    onChange={(e) => setSelectedPlaybookId(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-sm text-white/85 outline-none"
                  >
                    <option value="">Select…</option>
                    {playbooks.map((pb) => (
                      <option key={pb.id} value={pb.id}>
                        {pb.name}
                      </option>
                    ))}
                  </select>
                  <div className="mt-1 text-xs text-white/55">
                    If a playbook has <span className="font-mono">requires_approval</span>, it will be created as{" "}
                    <span className="font-mono">requires_approval</span> and must be approved.
                  </div>
                </label>
              ) : (
                <label className="block">
                  <div className="text-xs text-white/60">Action</div>
                  <select
                    value={action}
                    onChange={(e) => setAction(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-sm text-white/85 outline-none"
                  >
                    {actionOptions.map((a) => (
                      <option key={a.value} value={a.value}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              {mode === "action" && action === "CONFIG_SCAN" ? (
                <label className="block">
                  <div className="text-xs text-white/60">Asset ID (optional)</div>
                  <input
                    value={assetId}
                    onChange={(e) => setAssetId(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                    placeholder="asset uuid"
                  />
                </label>
              ) : null}

              {mode === "action" && action === "CORRELATE_ALERTS" ? (
                <label className="block">
                  <div className="text-xs text-white/60">Threshold</div>
                  <input
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                    type="number"
                    min={1}
                    className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  />
                </label>
              ) : null}

              {mode === "action" && needsUpload ? (
                <label className="block">
                  <div className="text-xs text-white/60">Upload File</div>
                  <input
                    type="file"
                    className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none"
                    onChange={(e) => onUploadSelected(e.target.files?.[0] ?? null)}
                  />
                  <div className="mt-1 text-xs text-white/55">
                    {upload ? (
                      <>
                        uploaded: <span className="font-mono">{upload.filename}</span> (<span className="font-mono">{upload.id}</span>)
                      </>
                    ) : (
                      "Upload CSV/JSON for IMPORT_ASSETS, text/JSON for intel, any text artifact for config scan."
                    )}
                  </div>
                </label>
              ) : null}

              {mode === "playbook" ? (
                <label className="block">
                  <div className="text-xs text-white/60">Optional Upload (for params)</div>
                  <input
                    type="file"
                    className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none"
                    onChange={(e) => onUploadSelected(e.target.files?.[0] ?? null)}
                  />
                  <div className="mt-1 text-xs text-white/55">
                    If provided, execution params include <span className="font-mono">upload_id</span>.
                  </div>
                </label>
              ) : null}

              {error ? (
                <div className="rounded-xl border border-ember-400/30 bg-ember-500/10 px-3 py-2 text-sm text-ember-300">
                  {error}
                </div>
              ) : null}

              <button
                disabled={busy}
                className="w-full rounded-xl bg-neon-500 px-3 py-2 text-sm font-semibold text-black hover:bg-neon-400 disabled:opacity-50"
              >
                {busy ? "Working…" : "Run"}
              </button>
            </form>
          </Card>
        </div>
      </div>
    </RequireAuth>
  );
}

