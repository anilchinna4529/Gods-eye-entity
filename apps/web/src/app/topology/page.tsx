"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { RequireAuth } from "@/components/RequireAuth";
import { Card } from "@/components/Card";
import { apiFetch } from "@/lib/api";
import type { Asset, Relationship } from "@/lib/types";

type Node = { id: string; label: string };
type Link = { source: string; target: string; kind: string };

export default function TopologyPage() {
  const ref = useRef<SVGSVGElement | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [rels, setRels] = useState<Relationship[]>([]);

  useEffect(() => {
    Promise.all([apiFetch<Asset[]>("/assets?limit=500"), apiFetch<Relationship[]>("/relationships")])
      .then(([a, r]) => {
        setAssets(a);
        setRels(r);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;

    const nodes: Node[] = assets.map((a) => ({ id: a.id, label: a.hostname }));
    const links: Link[] = rels.map((r) => ({ source: r.from_asset_id, target: r.to_asset_id, kind: r.kind }));

    const width = 980;
    const height = 560;

    const root = d3.select(svg);
    root.selectAll("*").remove();
    root.attr("viewBox", `0 0 ${width} ${height}`);

    const g = root.append("g");

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.35, 3])
      .on("zoom", (event) => g.attr("transform", event.transform.toString()));
    root.call(zoom as any);

    const link = g
      .append("g")
      .attr("stroke", "rgba(255,255,255,0.18)")
      .attr("stroke-width", 1)
      .selectAll("line")
      .data(links)
      .join("line");

    const node = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(
        d3
          .drag<SVGGElement, Node>()
          .on("start", (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            (d as any).fx = (d as any).x;
            (d as any).fy = (d as any).y;
          })
          .on("drag", (event, d) => {
            (d as any).fx = event.x;
            (d as any).fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) sim.alphaTarget(0);
            (d as any).fx = null;
            (d as any).fy = null;
          }) as any
      );

    node
      .append("circle")
      .attr("r", 10)
      .attr("fill", "rgba(46,230,166,0.85)")
      .attr("stroke", "rgba(255,255,255,0.25)")
      .attr("stroke-width", 1);

    node
      .append("text")
      .text((d) => d.label)
      .attr("x", 14)
      .attr("y", 4)
      .attr("fill", "rgba(255,255,255,0.85)")
      .attr("font-size", 12)
      .attr("font-family", "var(--font-display)");

    const sim = d3
      .forceSimulation(nodes as any)
      .force("link", d3.forceLink(links as any).id((d: any) => d.id).distance(90))
      .force("charge", d3.forceManyBody().strength(-220))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(20));

    sim.on("tick", () => {
      link
        .attr("x1", (d: any) => (d.source as any).x)
        .attr("y1", (d: any) => (d.source as any).y)
        .attr("x2", (d: any) => (d.target as any).x)
        .attr("y2", (d: any) => (d.target as any).y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      sim.stop();
    };
  }, [assets, rels]);

  return (
    <RequireAuth>
      <Card title="Network Topology (Assets + Relationships)">
        <div className="text-sm text-white/65 mb-3">
          Drag nodes to reposition. Zoom and pan supported.
        </div>
        <div className="overflow-hidden rounded-2xl border border-[var(--stroke)] bg-black/20">
          <svg ref={ref} className="h-[560px] w-full" />
        </div>
      </Card>
    </RequireAuth>
  );
}
