/** Turns the bundled career graph into nodes/links for the KnowledgeGraph component. */
import type { GraphLink, GraphNode } from "@/components/ui/knowledge-graph";
import { graphSnapshot, skills, type NodeLabel } from "@/data/careerGraph";

export const labelColor: Record<NodeLabel, string> = {
  Person: "hsl(71 78% 50%)",
  Role: "hsl(199 89% 60%)",
  Company: "hsl(262 83% 70%)",
  Project: "hsl(32 95% 58%)",
  Skill: "hsl(0 0% 62%)",
  Education: "hsl(330 81% 66%)",
};

const baseSize: Record<NodeLabel, number> = { Person: 26, Role: 17, Company: 13, Project: 11, Skill: 6, Education: 13 };
const skillUsage = new Map(skills.map((s) => [s.id, s.usage]));

/** Edge ids match the backend's `{source}-{type}-{target}` so chat highlights line up. */
export const edgeId = (source: string, type: string, target: string) => `${source}-${type}-${target}`;

export const graphNodes: GraphNode[] = graphSnapshot.nodes.map((n) => ({
  id: n.id,
  label: n.name,
  type: n.label,
  color: labelColor[n.label],
  size: n.label === "Skill" ? baseSize.Skill + Math.min(9, (skillUsage.get(n.id) ?? 0) * 0.8) : baseSize[n.label],
  data: n,
}));

export const graphLinks: GraphLink[] = graphSnapshot.relationships.map((r) => ({
  id: edgeId(r.source, r.type, r.target),
  source: r.source,
  target: r.target,
  label: r.type,
}));

export const graphLegend = (Object.keys(labelColor) as NodeLabel[]).map((type) => ({ type, color: labelColor[type] }));
