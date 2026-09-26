/**
 * Typed read access to the career graph dataset shared with the backend
 * (backend/data/career_graph.json). The site's projects, roles and skills all
 * come from here, so the portfolio and the chatbot can never disagree.
 */
import raw from "@data/career_graph.json";

export type NodeLabel = "Person" | "Role" | "Company" | "Project" | "Skill" | "Education";
export type ProjectKind = "work" | "freelance" | "personal";
export type SkillCategory = "AI/ML" | "Backend" | "Data" | "Cloud & DevOps" | "Frontend" | "Tooling";

export interface GraphNodeRecord {
  label: NodeLabel;
  id: string;
  name: string;
  [property: string]: string | number | undefined;
}

export interface GraphRelationshipRecord {
  type: string;
  source: string;
  target: string;
}

export interface Skill {
  id: string;
  name: string;
  category: SkillCategory;
  /** How many projects and roles use this skill: a measure of evidence, not proficiency. */
  usage: number;
}

export interface Project {
  id: string;
  name: string;
  summary: string;
  kind: ProjectKind;
  year: number;
  repoUrl?: string;
  demoUrl?: string;
  skills: Skill[];
  roleId?: string;
  clientName?: string;
}

export interface Role {
  id: string;
  title: string;
  company: string;
  start?: string;
  end?: string;
  employmentType: string;
  location?: string;
  summary: string;
  skills: Skill[];
}

const nodes = raw.nodes as GraphNodeRecord[];
const relationships = raw.relationships as GraphRelationshipRecord[];
const byId = new Map(nodes.map((node) => [node.id, node]));

const targetsOf = (source: string, type: string) =>
  relationships.filter((r) => r.source === source && r.type === type).map((r) => byId.get(r.target)!);

const usageCount = new Map<string, number>();
for (const rel of relationships) {
  if (rel.type === "USES") usageCount.set(rel.target, (usageCount.get(rel.target) ?? 0) + 1);
}

const toSkill = (node: GraphNodeRecord): Skill => ({
  id: node.id,
  name: node.name,
  category: node.category as SkillCategory,
  usage: usageCount.get(node.id) ?? 0,
});

const bySkillUsage = (a: Skill, b: Skill) => b.usage - a.usage || a.name.localeCompare(b.name);

export const skills: Skill[] = nodes.filter((n) => n.label === "Skill").map(toSkill).sort(bySkillUsage);

export const projects: Project[] = nodes
  .filter((n) => n.label === "Project")
  .map((n) => ({
    id: n.id,
    name: n.name,
    summary: String(n.summary ?? ""),
    kind: n.kind as ProjectKind,
    year: Number(n.year),
    repoUrl: n.repo_url as string | undefined,
    demoUrl: n.demo_url as string | undefined,
    skills: targetsOf(n.id, "USES").map(toSkill).sort(bySkillUsage),
    roleId: targetsOf(n.id, "BUILT_DURING")[0]?.id,
    clientName: targetsOf(n.id, "FOR_CLIENT")[0]?.name,
  }));

export const roles: Role[] = nodes
  .filter((n) => n.label === "Role")
  .map((n) => ({
    id: n.id,
    title: n.name,
    company: targetsOf(n.id, "AT_COMPANY").map((c) => c.name).join(", "),
    start: n.start as string | undefined,
    end: n.end as string | undefined,
    employmentType: String(n.employment_type ?? ""),
    location: n.location as string | undefined,
    summary: String(n.summary ?? ""),
    skills: targetsOf(n.id, "USES").map(toSkill).sort(bySkillUsage),
  }));

export const projectById = (id: string): Project => {
  const project = projects.find((p) => p.id === id);
  if (!project) throw new Error(`Unknown project id in site content: ${id}`);
  return project;
};

export const roleById = (id: string): Role => {
  const role = roles.find((r) => r.id === id);
  if (!role) throw new Error(`Unknown role id in site content: ${id}`);
  return role;
};

export const skillsByCategory = (): Map<SkillCategory, Skill[]> => {
  const grouped = new Map<SkillCategory, Skill[]>();
  for (const skill of skills) grouped.set(skill.category, [...(grouped.get(skill.category) ?? []), skill]);
  return grouped;
};

/** The raw graph, for rendering the knowledge graph before (or without) the API. */
export const graphSnapshot = { nodes, relationships };

export const graphStats = {
  nodes: nodes.length,
  relationships: relationships.length,
  projects: projects.length,
  skills: skills.length,
};
