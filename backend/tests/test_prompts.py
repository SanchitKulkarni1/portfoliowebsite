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
    rows = tuple({"name": "x" * 100} for _ in range(100))
    prompt = prompts.answer_prompt("q", rows, max_chars=500)
    assert prompt.endswith("…(truncated)")
    assert len(prompt) < 700
