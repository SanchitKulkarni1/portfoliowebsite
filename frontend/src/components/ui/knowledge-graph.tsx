/**
 * Force-directed knowledge graph. Adapted from 21st.dev "Knowledge Graph" (heygaia):
 * - dark canvas, colours per node type supplied by the caller
 * - `highlight` dims everything except the given nodes/edges and zooms to them,
 *   without restarting the simulation (a separate, cheap effect restyles the SVG)
 * - labels shown in full for large or highlighted nodes
 */
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import * as d3 from "d3";
import { cn } from "@/lib/utils";

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: string;
  size?: number;
  color?: string;
  data?: unknown;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  id: string;
  source: string | GraphNode;
  target: string | GraphNode;
  label?: string;
}

export interface GraphHighlight {
  nodeIds: ReadonlySet<string>;
  edgeIds: ReadonlySet<string>;
}

export interface KnowledgeGraphProps {
  nodes: GraphNode[];
  links: GraphLink[];
  highlight?: GraphHighlight | null;
  selectedId?: string | null;
  onNodeClick?: (node: GraphNode) => void;
  legend?: Array<{ type: string; color: string }>;
  className?: string;
}

export interface KnowledgeGraphHandle {
  resetZoom: () => void;
}

const LABEL_ALWAYS_SIZE = 16;
const endpoint = (end: string | GraphNode) => (typeof end === "string" ? end : end.id);

export const KnowledgeGraph = forwardRef<KnowledgeGraphHandle, KnowledgeGraphProps>(
  ({ nodes, links, highlight, selectedId, onNodeClick, legend, className }, ref) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
    const simNodesRef = useRef<GraphNode[]>([]);
    const onClickRef = useRef(onNodeClick);
    onClickRef.current = onNodeClick;
    const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

    const fitTo = (ids: ReadonlySet<string> | null, duration = 750) => {
      const svg = svgRef.current;
      const container = containerRef.current;
      if (!svg || !container || !zoomRef.current) return;
      const pts = simNodesRef.current.filter((n) => !ids || ids.has(n.id));
      if (pts.length === 0) return;
      const xs = pts.map((n) => n.x ?? 0);
      const ys = pts.map((n) => n.y ?? 0);
      const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      const { clientWidth: w, clientHeight: h } = container;
      const pad = 90;
      const scale = Math.min(1.6, 0.9 / Math.max((x1 - x0 + pad) / w, (y1 - y0 + pad) / h));
      const transform = d3.zoomIdentity
        .translate(w / 2, h / 2)
        .scale(scale)
        .translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
      d3.select(svg).transition().duration(duration).call(zoomRef.current.transform, transform);
    };

    useImperativeHandle(ref, () => ({ resetZoom: () => fitTo(null) }));

    // Build the simulation once per dataset.
    useEffect(() => {
      const svgEl = svgRef.current;
      const container = containerRef.current;
      if (!svgEl || !container || nodes.length === 0) return;

      const svg = d3.select(svgEl);
      svg.selectAll("*").remove();
      const { clientWidth: width, clientHeight: height } = container;

      const simNodes: GraphNode[] = nodes.map((n) => ({ ...n, size: n.size ?? 10 }));
      const simLinks: GraphLink[] = links.map((l) => ({ ...l }));
      simNodesRef.current = simNodes;

      const g = svg.append("g");
      const zoom = d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.15, 4])
        .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
          g.attr("transform", event.transform.toString());
          // Keep labels ~11px on screen at any zoom level.
          g.selectAll<SVGTextElement, GraphNode>(".kg-label")
            .attr("font-size", 11 / event.transform.k)
            .attr("stroke-width", 3 / event.transform.k);
        });
      zoomRef.current = zoom;
      svg.call(zoom).on("dblclick.zoom", null);

      const simulation = d3
        .forceSimulation<GraphNode>(simNodes)
        .force(
          "link",
          d3
            .forceLink<GraphNode, GraphLink>(simLinks)
            .id((d) => d.id)
            .distance((l) => 40 + ((l.target as GraphNode).size ?? 10) * 2.5)
            .strength(0.5),
        )
        .force("charge", d3.forceManyBody<GraphNode>().strength((d) => -60 - (d.size ?? 10) * 12))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide<GraphNode>().radius((d) => (d.size ?? 10) + 6));

      const link = g
        .append("g")
        .selectAll<SVGLineElement, GraphLink>("line")
        .data(simLinks)
        .join("line")
        .attr("class", "kg-link")
        .attr("stroke", "hsl(0 0% 100%)")
        .attr("stroke-opacity", 0.12)
        .attr("stroke-width", 1.2);

      const nodeGroup = g
        .append("g")
        .selectAll<SVGGElement, GraphNode>("g")
        .data(simNodes)
        .join("g")
        .attr("class", "kg-node")
        .style("cursor", "pointer")
        .call(
          d3
            .drag<SVGGElement, GraphNode>()
            .on("start", (event, d) => {
              if (!event.active) simulation.alphaTarget(0.3).restart();
              d.fx = d.x;
              d.fy = d.y;
            })
            .on("drag", (event, d) => {
              d.fx = event.x;
              d.fy = event.y;
            })
            .on("end", (event, d) => {
              if (!event.active) simulation.alphaTarget(0);
              d.fx = null;
              d.fy = null;
            }),
        );

      nodeGroup
        .append("circle")
        .attr("class", "kg-halo")
        .attr("r", (d) => (d.size ?? 10) + 7)
        .attr("fill", (d) => d.color ?? "#888")
        .attr("opacity", 0);

      nodeGroup
        .append("circle")
        .attr("class", "kg-dot")
        .attr("r", (d) => d.size ?? 10)
        .attr("fill", (d) => d.color ?? "#888")
        .attr("stroke", "#050505")
        .attr("stroke-width", 2);

      nodeGroup
        .append("text")
        .attr("class", "kg-label")
        .attr("text-anchor", "middle")
        .attr("dy", (d) => (d.size ?? 10) + 13)
        .attr("font-size", 11)
        .attr("font-family", "Inter, sans-serif")
        .attr("fill", "hsl(0 0% 88%)")
        .attr("stroke", "#050505")
        .attr("stroke-width", 3)
        .attr("paint-order", "stroke")
        .attr("stroke-linejoin", "round")
        .attr("pointer-events", "none")
        .attr("opacity", (d) => ((d.size ?? 10) >= LABEL_ALWAYS_SIZE ? 1 : 0))
        .text((d) => d.label);

      nodeGroup
        .on("click", (_event, d) => onClickRef.current?.(d))
        .on("mouseover", (event: MouseEvent, d) => {
          const [x, y] = d3.pointer(event, container);
          setTooltip({ x: x + 12, y: y - 12, text: `${d.label} · ${d.type}` });
        })
        .on("mouseout", () => setTooltip(null));

      simulation.on("tick", () => {
        link
          .attr("x1", (d) => (d.source as GraphNode).x ?? 0)
          .attr("y1", (d) => (d.source as GraphNode).y ?? 0)
          .attr("x2", (d) => (d.target as GraphNode).x ?? 0)
          .attr("y2", (d) => (d.target as GraphNode).y ?? 0);
        nodeGroup.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });
      simulation.on("end", () => fitTo(null, 600));

      return () => {
        simulation.stop();
      };
    }, [nodes, links]);

    // Restyle for highlight/selection without touching the simulation.
    useEffect(() => {
      const svgEl = svgRef.current;
      if (!svgEl) return;
      const svg = d3.select(svgEl);
      const active = highlight && highlight.nodeIds.size > 0 ? highlight : null;
      const isOn = (id: string) => !active || active.nodeIds.has(id) || id === selectedId;

      svg
        .selectAll<SVGGElement, GraphNode>(".kg-node")
        .transition()
        .duration(400)
        .attr("opacity", (d) => (isOn(d.id) ? 1 : 0.12));
      svg
        .selectAll<SVGCircleElement, GraphNode>(".kg-halo")
        .transition()
        .duration(400)
        .attr("opacity", (d) => ((active && active.nodeIds.has(d.id)) || d.id === selectedId ? 0.28 : 0));
      svg
        .selectAll<SVGTextElement, GraphNode>(".kg-label")
        .transition()
        .duration(400)
        .attr("opacity", (d) =>
          (active && active.nodeIds.has(d.id)) || d.id === selectedId || (!active && (d.size ?? 10) >= LABEL_ALWAYS_SIZE) ? 1 : 0,
        );
      svg
        .selectAll<SVGLineElement, GraphLink>(".kg-link")
        .transition()
        .duration(400)
        .attr("stroke", (d) => (active?.edgeIds.has(d.id) ? "hsl(71 78% 50%)" : "hsl(0 0% 100%)"))
        .attr("stroke-opacity", (d) => {
          if (!active) return 0.12;
          if (active.edgeIds.has(d.id)) return 0.9;
          return active.nodeIds.has(endpoint(d.source)) && active.nodeIds.has(endpoint(d.target)) ? 0.25 : 0.03;
        })
        .attr("stroke-width", (d) => (active?.edgeIds.has(d.id) ? 2 : 1.2));

      if (active) fitTo(active.nodeIds);
    }, [highlight, selectedId]);

    return (
      <div className={cn("relative h-full w-full", className)}>
        <div ref={containerRef} className="h-full w-full">
          <svg ref={svgRef} width="100%" height="100%" role="img" aria-label="Interactive graph of Sanchit's career" />
        </div>

        {tooltip && (
          <div
            className="pointer-events-none absolute z-10 rounded-md border border-white/10 bg-black/90 px-2.5 py-1.5 font-mono text-xs text-neutral-200 shadow-lg"
            style={{ left: tooltip.x, top: tooltip.y }}
          >
            {tooltip.text}
          </div>
        )}

        {legend && legend.length > 0 && (
          <div className="absolute bottom-3 left-3 z-10 hidden flex-wrap gap-x-3 gap-y-1.5 sm:flex rounded-lg border border-white/10 bg-black/70 px-3 py-2 backdrop-blur-sm">
            {legend.map((item) => (
              <span key={item.type} className="flex items-center gap-1.5 font-mono text-[11px] text-neutral-300">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                {item.type}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  },
);

KnowledgeGraph.displayName = "KnowledgeGraph";
