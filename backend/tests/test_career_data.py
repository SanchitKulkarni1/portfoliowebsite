from pathlib import Path

import pytest

from app.domain.career_data import load_career_data, parse_career_data
from app.domain.errors import InvalidCareerDataError

DATA = Path(__file__).resolve().parent.parent / "data" / "career_graph.json"


def test_bundled_dataset_is_valid():
    dataset = load_career_data(DATA)
    labels = {node.label for node in dataset.nodes}
    assert labels == {"Person", "Role", "Company", "Project", "Skill", "Education"}
    assert sum(1 for n in dataset.nodes if n.label == "Person") == 1


def test_every_skill_is_backed_by_a_project_or_role():
    dataset = load_career_data(DATA)
    used = {rel.target for rel in dataset.relationships if rel.type == "USES"}
    orphans = [n.id for n in dataset.nodes if n.label == "Skill" and n.id not in used]
    assert orphans == []


def test_every_project_is_linked_to_sanchit():
    dataset = load_career_data(DATA)
    built = {rel.target for rel in dataset.relationships if rel.type == "BUILT"}
    assert [n.id for n in dataset.nodes if n.label == "Project" and n.id not in built] == []


def test_client_links_only_come_from_freelance_projects():
    dataset = load_career_data(DATA)
    kinds = {n.id: n.properties.get("kind") for n in dataset.nodes if n.label == "Project"}
    for_client = [rel.source for rel in dataset.relationships if rel.type == "FOR_CLIENT"]
    assert for_client and all(kinds[source] == "freelance" for source in for_client)


@pytest.mark.parametrize(
    "raw,message",
    [
        ({"nodes": [{"label": "Pet", "id": "x", "name": "x"}]}, "unknown label"),
        ({"nodes": [{"label": "Skill", "id": "x"}]}, "missing name"),
        ({"nodes": [{"label": "Skill", "id": "x", "name": "X", "colour": "red"}]}, "not in schema"),
        (
            {"nodes": [{"label": "Skill", "id": "x", "name": "X"}, {"label": "Skill", "id": "x", "name": "Y"}]},
            "duplicate id",
        ),
        (
            {
                "nodes": [{"label": "Skill", "id": "x", "name": "X"}],
                "relationships": [{"type": "USES", "source": "x", "target": "y"}],
            },
            "endpoint does not exist",
        ),
        (
            {
                "nodes": [{"label": "Skill", "id": "a", "name": "A"}, {"label": "Skill", "id": "b", "name": "B"}],
                "relationships": [{"type": "USES", "source": "a", "target": "b"}],
            },
            "not in the schema",
        ),
    ],
)
def test_invalid_data_is_rejected(raw, message):
    with pytest.raises(InvalidCareerDataError, match=message):
        parse_career_data(raw)
