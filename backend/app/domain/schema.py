"""The career graph schema: the single source of truth for labels, properties and
relationship types. The seed validator, the Cypher guard and the LLM prompt all
read from here, so they can never drift apart."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeType:
    label: str
    properties: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class RelationshipType:
    type: str
    source: str
    target: str
    description: str


# Every node carries `id` (a stable slug) and `name` (a display name).
BASE_PROPERTIES = ("id", "name")

NODE_TYPES: tuple[NodeType, ...] = (
    NodeType(
        "Person", ("headline", "location", "summary"), "Sanchit Kulkarni himself (exactly one node, id 'sanchit')."
    ),
    NodeType(
        "Role",
        ("start", "end", "employment_type", "summary"),
        "A job held. `name` is the job title; start/end are 'YYYY-MM' strings, end is 'present' for the current role.",
    ),
    NodeType("Company", ("industry", "location"), "An employer or client organisation."),
    NodeType(
        "Project",
        ("summary", "kind", "year", "repo_url", "demo_url"),
        "Something Sanchit built. kind is one of 'work', 'freelance', 'personal'. year is an integer.",
    ),
    NodeType(
        "Skill",
        ("category",),
        "A technology or technique. category is one of 'AI/ML', 'Backend', 'Data', 'Cloud & DevOps', 'Frontend', 'Tooling'.",
    ),
    NodeType("Education", ("degree", "start", "end", "grade"), "A degree programme. `name` is the institution."),
)

RELATIONSHIP_TYPES: tuple[RelationshipType, ...] = (
    RelationshipType("HELD", "Person", "Role", "Sanchit held this role."),
    RelationshipType("AT_COMPANY", "Role", "Company", "The role was at this company."),
    RelationshipType("BUILT", "Person", "Project", "Sanchit built this project."),
    RelationshipType("BUILT_DURING", "Project", "Role", "The project was built as part of this role."),
    RelationshipType("USES", "Project", "Skill", "The project uses this skill."),
    RelationshipType("USES", "Role", "Skill", "The role involved this skill."),
    RelationshipType("STUDIED_AT", "Person", "Education", "Sanchit studied here."),
)

NODE_LABELS: frozenset[str] = frozenset(t.label for t in NODE_TYPES)
RELATIONSHIP_NAMES: frozenset[str] = frozenset(r.type for r in RELATIONSHIP_TYPES)


def node_type(label: str) -> NodeType:
    for candidate in NODE_TYPES:
        if candidate.label == label:
            return candidate
    raise KeyError(label)


def allowed_properties(label: str) -> frozenset[str]:
    return frozenset(BASE_PROPERTIES + node_type(label).properties)


def is_valid_relationship(rel_type: str, source_label: str, target_label: str) -> bool:
    return any(r.type == rel_type and r.source == source_label and r.target == target_label for r in RELATIONSHIP_TYPES)


def describe_schema() -> str:
    """Render the schema as compact text for LLM prompts (structure only, no data)."""
    lines = ["Node labels (every node has `id` and `name`):"]
    for t in NODE_TYPES:
        props = ", ".join(t.properties)
        lines.append(f"- :{t.label} {{{props}}}: {t.description}")
    lines.append("Relationships:")
    for r in RELATIONSHIP_TYPES:
        lines.append(f"- (:{r.source})-[:{r.type}]->(:{r.target}): {r.description}")
    return "\n".join(lines)
