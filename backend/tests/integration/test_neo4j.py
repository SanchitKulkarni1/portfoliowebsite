"""Integration tests against a real Neo4j. WIPES the target database.

Run with:  NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=... pytest -m integration
Point this at a throwaway instance, never at the production Aura database.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncGraphDatabase

from app.config import Settings
from app.container import Container, build_rate_limiter
from app.domain.career_data import load_career_data
from app.domain.errors import QueryExecutionError
from app.domain.models import SafeCypher
from app.infrastructure.neo4j_repository import Neo4jGraphRepository, create_driver
from app.infrastructure.neo4j_seeder import Neo4jSeeder
from app.main import create_app
from app.services.chat_service import ChatService
from app.services.cypher_guard import CypherGuard
from app.services.graph_service import GraphService
from app.services.prompts import FEW_SHOT_EXAMPLES
from tests.fakes import FakeLanguageModel

URI = os.getenv("NEO4J_TEST_URI")
USER = os.getenv("NEO4J_TEST_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "password")
DATASET = load_career_data(Path(__file__).resolve().parents[2] / "data" / "career_graph.json")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not URI, reason="set NEO4J_TEST_URI to run Neo4j integration tests"),
]


@pytest.fixture(scope="module")
async def driver():
    driver = AsyncGraphDatabase.driver(URI, auth=(USER, PASSWORD))
    await Neo4jSeeder(driver, database="neo4j").replace_graph(DATASET)
    yield driver
    await driver.close()


@pytest.fixture
def repository(driver):
    return Neo4jGraphRepository(driver, database="neo4j", timeout_seconds=5)


async def test_seeding_is_idempotent(driver):
    await Neo4jSeeder(driver, database="neo4j").replace_graph(DATASET)
    records, _, _ = await driver.execute_query("MATCH (n) RETURN count(n) AS nodes")
    assert records[0]["nodes"] == len(DATASET.nodes)
    records, _, _ = await driver.execute_query("MATCH ()-[r]->() RETURN count(r) AS rels")
    assert records[0]["rels"] == len(DATASET.relationships)


async def test_snapshot_matches_dataset(repository):
    snapshot = await repository.fetch_snapshot()
    assert {n.id for n in snapshot.nodes} == {n.id for n in DATASET.nodes}
    assert len(snapshot.edges) == len(DATASET.relationships)


@pytest.mark.parametrize("question,query", FEW_SHOT_EXAMPLES)
async def test_few_shot_examples_return_highlightable_results(repository, question, query):
    result = await repository.run_read(CypherGuard(max_rows=50).validate(query))
    assert result.rows, question
    assert result.subgraph.nodes, question


async def test_relationships_resolve_to_node_ids(repository):
    safe = CypherGuard(max_rows=50).validate(FEW_SHOT_EXAMPLES[0][1])  # Evenflow projects
    result = await repository.run_read(safe)
    node_ids = {n.id for n in result.subgraph.nodes}
    assert {"evenflow-brands", "role-evenflow", "evenflow-price-intelligence"} <= node_ids
    assert all(e.source in node_ids and e.target in node_ids for e in result.subgraph.edges)
    assert {e.type for e in result.subgraph.edges} == {"AT_COMPANY", "BUILT_DURING"}
    first_row = result.rows[0]
    assert first_row["c"]["name"] == "Evenflow Brands"
    assert first_row["a"] == {"type": "AT_COMPANY", "source": "role-evenflow", "target": "evenflow-brands"}


async def test_database_blocks_writes_even_if_the_guard_is_bypassed(repository, driver):
    # SafeCypher is normally only created by CypherGuard; constructing it directly
    # simulates a guard bug. The read-only transaction must still stop the write.
    with pytest.raises(QueryExecutionError, match="read access mode"):
        await repository.run_read(SafeCypher("MATCH (n) DETACH DELETE n RETURN count(*)"))
    records, _, _ = await driver.execute_query("MATCH (n) RETURN count(n) AS nodes")
    assert records[0]["nodes"] == len(DATASET.nodes)


async def test_syntax_errors_become_query_execution_errors(repository):
    with pytest.raises(QueryExecutionError):
        await repository.run_read(SafeCypher("MATCH (n:Skill RETURN n"))


async def test_ping(repository):
    assert await repository.ping()


def test_full_http_stack_with_real_neo4j(driver):
    """Real FastAPI + real Neo4j; only the LLM is scripted."""
    llm = FakeLanguageModel([FEW_SHOT_EXAMPLES[1][1], "Several projects use LangGraph."])
    settings = Settings(neo4j_uri=URI, neo4j_user=USER, neo4j_password=PASSWORD, google_api_key="unused")

    async def factory(s: Settings) -> Container:
        app_driver = create_driver(URI, USER, PASSWORD)
        repo = Neo4jGraphRepository(app_driver, database="neo4j", timeout_seconds=5)
        return Container(
            chat_service=ChatService(llm, repo, CypherGuard(max_rows=50)),
            graph_service=GraphService(repo, snapshot_ttl_seconds=60),
            chat_rate_limiter=build_rate_limiter(s),
            close=app_driver.close,
        )

    with TestClient(create_app(settings, container_factory=factory)) as client:
        chat = client.post("/api/v1/chat", json={"question": "Which projects use LangGraph?"}).json()
        graph = client.get("/api/v1/graph").json()
        ready = client.get("/health/ready")

    assert chat["status"] == "answered"
    projects = {n["id"] for n in chat["nodes"] if n["label"] == "Project"}
    assert {
        "giteq",
        "dodgeai-fde",
        "market-research-copilot",
        "ai-sales-agent",
        "dynamic-pricing-agent",
        "recall",
    } == projects
    assert all(e["type"] == "USES" and e["target"] == "langgraph" for e in chat["edges"])
    assert len(graph["nodes"]) == len(DATASET.nodes)
    assert ready.status_code == 200


async def test_role_locations_are_queryable(repository):
    safe = CypherGuard(max_rows=50).validate(
        "MATCH (:Person {id: 'sanchit'})-[h:HELD]->(r:Role) WHERE r.location = 'Remote' RETURN r"
    )
    result = await repository.run_read(safe)
    assert {n.id for n in result.subgraph.nodes} == {"role-ascent", "role-tmlc"}


async def test_exported_cypher_script_builds_the_same_graph(driver, repository):
    """scripts/export_cypher.py output (for pasting into the Aura console) must equal the seeder's result."""
    from scripts.export_cypher import to_cypher

    await Neo4jSeeder(driver, database="neo4j").replace_graph(DATASET)
    seeded = await repository.fetch_snapshot()

    script = to_cypher(DATASET)
    statements = [s.strip() for s in script.split(";\n") if s.strip() and not s.strip().startswith("//")]
    for statement in statements:
        body = "\n".join(line for line in statement.splitlines() if not line.startswith("//"))
        records, _, _ = await driver.execute_query(body)
    assert records[0]["nodes"] == len(DATASET.nodes)
    assert records[0]["relationships"] == len(DATASET.relationships)

    exported = await repository.fetch_snapshot()
    assert sorted(exported.nodes, key=lambda n: n.id) == sorted(seeded.nodes, key=lambda n: n.id)
    assert sorted(e.id for e in exported.edges) == sorted(e.id for e in seeded.edges)


@pytest.mark.skipif(not os.getenv("NEO4J_TEST_HTTP_URL"), reason="set NEO4J_TEST_HTTP_URL to test the Query API seeder")
async def test_http_seeder_builds_the_same_graph(driver, repository):
    from app.infrastructure.neo4j_http_seeder import Neo4jHttpSeeder

    await Neo4jSeeder(driver, database="neo4j").replace_graph(DATASET)
    seeded = await repository.fetch_snapshot()

    summary = await Neo4jHttpSeeder(
        base_url=os.environ["NEO4J_TEST_HTTP_URL"], database="neo4j", user=USER, password=PASSWORD
    ).replace_graph(DATASET)

    assert (summary.nodes, summary.relationships) == (len(DATASET.nodes), len(DATASET.relationships))
    exported = await repository.fetch_snapshot()
    assert sorted(exported.nodes, key=lambda n: n.id) == sorted(seeded.nodes, key=lambda n: n.id)
    assert sorted(e.id for e in exported.edges) == sorted(e.id for e in seeded.edges)


def test_query_api_url_is_derived_from_the_bolt_uri():
    from app.infrastructure.neo4j_http_seeder import query_api_base_url

    assert query_api_base_url("neo4j+s://5267a9c8.databases.neo4j.io") == "https://5267a9c8.databases.neo4j.io"
    assert query_api_base_url("bolt://127.0.0.1:7687") == "http://127.0.0.1:7474"
