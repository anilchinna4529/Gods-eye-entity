"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch } from "@/lib/api";
import type { Asset } from "@/lib/types";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [hostname, setHostname] = useState("");
  const [ip, setIp] = useState("");
  const [owner, setOwner] = useState("");
  const [tags, setTags] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const a = await apiFetch<Asset[]>("/assets?limit=500");
    setAssets(a);
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function createAsset(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await apiFetch<Asset>("/assets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hostname,
          ip: ip || null,
          owner: owner || null,
          tags: tags
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean),
          metadata: {}
        })
      });
      setHostname("");
      setIp("");
      setOwner("");
      setTags("");
      await refresh();
    } catch (err: any) {
      setError(err?.message ?? "Failed to create asset");
    }
  }

  return (
    <RequireAuth>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card title="Asset Inventory">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-white/60">
                  <tr>
                    <th className="py-2">Hostname</th>
                    <th className="py-2">IP</th>
                    <th className="py-2">Owner</th>
                    <th className="py-2">Tags</th>
                    <th className="py-2">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((a) => (
                    <tr key={a.id} className="border-t border-[var(--stroke)]">
                      <td className="py-2 font-medium">{a.hostname}</td>
                      <td className="py-2 font-mono text-xs text-white/75">{a.ip ?? "-"}</td>
                      <td className="py-2 text-white/75">{a.owner ?? "-"}</td>
                      <td className="py-2 text-white/75">{a.tags?.join(", ") || "-"}</td>
                      <td className="py-2 text-xs text-white/55">
                        {new Date(a.updated_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {assets.length === 0 ? (
                <div className="mt-3 text-sm text-white/65">No assets yet.</div>
              ) : null}
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Add Asset">
            <form className="space-y-3" onSubmit={createAsset}>
              <label className="block">
                <div className="text-xs text-white/60">Hostname</div>
                <input
                  value={hostname}
                  onChange={(e) => setHostname(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="web-01"
                />
              </label>
              <label className="block">
                <div className="text-xs text-white/60">IP (optional)</div>
                <input
                  value={ip}
                  onChange={(e) => setIp(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="10.0.0.10"
                />
              </label>
              <label className="block">
                <div className="text-xs text-white/60">Owner (optional)</div>
                <input
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="platform-team"
                />
              </label>
              <label className="block">
                <div className="text-xs text-white/60">Tags (comma-separated)</div>
                <input
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-neon-400"
                  placeholder="prod, linux, dmz"
                />
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

