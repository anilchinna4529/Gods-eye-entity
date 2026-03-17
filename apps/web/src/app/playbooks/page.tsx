"use client";

import { useEffect, useMemo, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch } from "@/lib/api";
import type { Playbook } from "@/lib/types";

const templates: Record<string, unknown> = {
  "Asset Import (CSV/JSON)": {
    version: 1,
    requires_approval: false,
    steps: [{ action: "IMPORT_ASSETS", params: { upload_id: "<upload_id>" } }]
  },
  "Threat Intel Ingest": {
    version: 1,
    requires_approval: false,
    steps: [{ action: "INGEST_INTEL", params: { upload_id: "<upload_id>", source: "local" } }]
  },
  "Config Secret Scan": {
    version: 1,
    requires_approval: false,
    steps: [{ action: "CONFIG_SCAN", params: { upload_id: "<upload_id>", asset_id: "<optional_asset_id>" } }]
  },
  "Correlation (Approval Gated)": {
    version: 1,
    requires_approval: true,
    steps: [{ action: "CORRELATE_ALERTS", params: { threshold: 3 } }]
  }
};

export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [definitionText, setDefinitionText] = useState(JSON.stringify(templates["Asset Import (CSV/JSON)"], null, 2));
  const [templateName, setTemplateName] = useState(Object.keys(templates)[0]);
  const [error, setError] = useState<string | null>(null);

  const parsed = useMemo(() => {
    try {
      return JSON.parse(definitionText) as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [definitionText]);

  async function refresh() {
    setPlaybooks(await apiFetch<Playbook[]>("/playbooks"));
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  function applyTemplate(next: string) {
    setTemplateName(next);
    setDefinitionText(JSON.stringify(templates[next], null, 2));
  }

  async function createPlaybook(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!parsed) {
      setError("Definition must be valid JSON.");
      return;
    }
    try {
      await apiFetch<Playbook>("/playbooks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, enabled, definition: parsed })
      });
      setName("");
      setDescription("");
      await refresh();
    } catch (err: any) {
      setError(err?.message ?? "Failed to create playbook");
    }
  }

  return (
    <RequireAuth>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card title="Playbooks">
            <div className="space-y-2">
              {playbooks.map((pb) => (
                <div key={pb.id} className="rounded-xl border border-[var(--stroke)] bg-black/20 px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium">{pb.name}</div>
                      <div className="text-xs text-white/60">{pb.description || "No description"}</div>
                      <div className="mt-2 text-xs text-white/55">
                        enabled: <span className="font-mono">{String(pb.enabled)}</span>
                      </div>
                    </div>
                    <pre className="max-h-40 max-w-[420px] overflow-auto rounded-lg border border-[var(--stroke)] bg-black/30 p-2 text-[11px] text-white/65">
                      {JSON.stringify(pb.definition, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
              {playbooks.length === 0 ? <div className="text-sm text-white/65">No playbooks yet.</div> : null}
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Create Playbook">
            <form className="space-y-3" onSubmit={createPlaybook}>
              <label className="block">
                <div className="text-xs text-white/60">Template</div>
                <select
                  value={templateName}
                  onChange={(e) => applyTemplate(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/25 px-3 py-2 text-sm text-white/85 outline-none"
                >
                  {Object.keys(templates).map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <div className="text-xs text-white/60">Name</div>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="nightly-config-scan"
                />
              </label>

              <label className="block">
                <div className="text-xs text-white/60">Description</div>
                <input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="Runs allowlisted scans on uploads."
                />
              </label>

              <label className="flex items-center gap-2 text-sm text-white/75">
                <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
                Enabled
              </label>

              <label className="block">
                <div className="text-xs text-white/60">Definition (JSON)</div>
                <textarea
                  value={definitionText}
                  onChange={(e) => setDefinitionText(e.target.value)}
                  className="mt-1 h-56 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 font-mono text-xs text-white/80 outline-none focus:border-neon-400"
                />
                <div className="mt-1 text-xs text-white/55">
                  Actions are allowlisted: <span className="font-mono">IMPORT_ASSETS</span>, <span className="font-mono">INGEST_INTEL</span>,{" "}
                  <span className="font-mono">CONFIG_SCAN</span>, <span className="font-mono">CORRELATE_ALERTS</span>.
                </div>
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

