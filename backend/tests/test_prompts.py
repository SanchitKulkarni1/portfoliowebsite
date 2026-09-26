import pytest

from app.domain.schema import NODE_LABELS, RELATIONSHIP_NAMES
from app.services import prompts


@pytest.mark.parametrize(
    "completion,expected",
    [
        ("MATCH (s:Skill) RETURN s", "MATCH (s:Skill) RETURN s"),
        ("```cypher\nMATCH (s:Skill) RETURN s\n```", "MATCH (s:Skill) RETURN s"),
        ("```\nMATCH (s:Skill) RETURN s```", "MATCH (s:Skill) RETURN s"),
        ("Cypher: MATCH (s:Skill) RETURN s", "MATCH (s:Skill) RETURN s"),
        ("NO_QUERY", None),
        ("  no_query.", None),
        ("", None),
    ],
)
def test_parse_cypher_completion(completion, expected):
    assert prompts.parse_cypher_completion(completion) == expected


def test_cypher_system_prompt_describes_the_whole_schema():
    for name in NODE_LABELS | RELATIONSHIP_NAMES:
        assert name in prompts.CYPHER_SYSTEM


def test_answer_prompt_truncates_large_results():
    rows = tuple({"name": f"{i}" + "x" * 100} for i in range(100))
    prompt = prompts.answer_prompt("q", rows, max_chars=500)
    assert prompt.endswith("…(truncated)")
    assert len(prompt) < 700


ROLE = {"label": "Role", "id": "role-freelance", "name": "Freelance", "summary": "long text " * 20}
CLIENT_A = {"label": "Company", "id": "a", "name": "A"}
CLIENT_B = {"label": "Company", "id": "b", "name": "B"}
PROJECT = {"label": "Project", "id": "p1", "name": "P1"}


def test_compact_results_lists_each_node_once_despite_cross_product_rows():
    rows = (
        {
            "p": PROJECT,
            "r": ROLE,
            "a": {"type": "AT_COMPANY", "source": "role-freelance", "target": "a"},
            "c": CLIENT_A,
        },
        {
            "p": PROJECT,
            "r": ROLE,
            "a": {"type": "AT_COMPANY", "source": "role-freelance", "target": "b"},
            "c": CLIENT_B,
        },
    )
    compact = prompts.compact_results(rows)
    assert [n["id"] for n in compact["nodes"]] == ["p1", "role-freelance", "a", "b"]
    assert compact["relationships"] == ["role-freelance -AT_COMPANY-> a", "role-freelance -AT_COMPANY-> b"]
    assert "values" not in compact


def test_compact_results_keeps_scalar_columns_with_their_nodes():
    rows = ({"s": {"label": "Skill", "id": "fastapi", "name": "FastAPI"}, "usage": 10},)
    assert prompts.compact_results(rows)["values"] == [{"for": ["fastapi"], "usage": 10}]


def test_compact_results_handles_property_only_queries():
    rows = ({"p.name": "gitEQ"}, {"p.name": "Recall"}, {"p.name": "gitEQ"})
    assert prompts.compact_results(rows)["values"] == [{"for": [], "p.name": "gitEQ"}, {"for": [], "p.name": "Recall"}]
