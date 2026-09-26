"""HTTP contract tests: the whole FastAPI stack with the ports replaced by fakes."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.container import Container, build_rate_limiter
from app.domain.errors import GraphUnavailableError, LanguageModelBusyError, LanguageModelError
from app.domain.models import GraphEdge, GraphNode, QueryResult, Subgraph
from app.main import create_app
from app.services.chat_service import ChatService
from app.services.cypher_guard import CypherGuard
from app.services.graph_service import GraphService
from tests.fakes import FakeGraphRepository, FakeLanguageModel

ORIGIN = "https://sanchitkulkarni.vercel.app"
ME = GraphNode("sanchit", "Person", "Sanchit Kulkarni")
GITEQ = GraphNode("giteq", "Project", "gitEQ", {"year": 2026})
BUILT = GraphEdge("sanchit", "giteq", "BUILT")
SUBGRAPH = Subgraph((ME, GITEQ), (BUILT,))


def settings(**overrides) -> Settings:
    values = dict(
        neo4j_uri="bolt://unused",
        neo4j_password="x",
        google_api_key="x",
        allowed_origins=ORIGIN,
        chat_rate_limit_requests=3,
    )
    values.update(overrides)
    return Settings(**values)


def client_for(llm: FakeLanguageModel, repo: FakeGraphRepository, **setting_overrides) -> TestClient:
    config = settings(**setting_overrides)

    async def factory(s: Settings) -> Container:
        return Container(
            chat_service=ChatService(llm, repo, CypherGuard(max_rows=50)),
            graph_service=GraphService(repo, snapshot_ttl_seconds=0),
            chat_rate_limiter=build_rate_limiter(s),
        )

    return TestClient(create_app(config, container_factory=factory))


def test_health():
    with client_for(FakeLanguageModel([]), FakeGraphRepository()) as client:
        assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("ready,code,body", [(True, 200, "up"), (False, 503, "down")])
def test_readiness(ready, code, body):
    with client_for(FakeLanguageModel([]), FakeGraphRepository(ready=ready)) as client:
        response = client.get("/health/ready")
    assert response.status_code == code
    assert response.json()["neo4j"] == body


def test_graph_snapshot_contract():
    with client_for(FakeLanguageModel([]), FakeGraphRepository(snapshot=SUBGRAPH)) as client:
        response = client.get("/api/v1/graph")
    assert response.status_code == 200
    assert response.json() == {
        "nodes": [
            {"id": "sanchit", "label": "Person", "name": "Sanchit Kulkarni", "properties": {}},
            {"id": "giteq", "label": "Project", "name": "gitEQ", "properties": {"year": 2026}},
        ],
        "edges": [{"id": "sanchit-BUILT-giteq", "source": "sanchit", "target": "giteq", "type": "BUILT"}],
    }


def test_chat_contract():
    llm = FakeLanguageModel(["MATCH (me:Person)-[b:BUILT]->(p:Project) RETURN me, b, p", "Sanchit built gitEQ."])
    repo = FakeGraphRepository([QueryResult(({"p": {"name": "gitEQ"}},), SUBGRAPH)])
    with client_for(llm, repo) as client:
        response = client.post("/api/v1/chat", json={"question": "  What   did you build? "})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["answer"] == "Sanchit built gitEQ."
    assert body["cypher"].endswith("LIMIT 50")
    assert [n["id"] for n in body["nodes"]] == ["sanchit", "giteq"]
    assert body["edges"][0]["id"] == "sanchit-BUILT-giteq"
    assert llm.calls[0][1] == "Question: What did you build?\nCypher:"  # whitespace normalised


@pytest.mark.parametrize(
    "payload", [{}, {"question": ""}, {"question": "   "}, {"question": "x" * 301}, {"question": 42}]
)
def test_chat_rejects_invalid_input_with_error_envelope(payload):
    with client_for(FakeLanguageModel([]), FakeGraphRepository()) as client:
        response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_chat_is_rate_limited_per_client():
    llm = FakeLanguageModel(["NO_QUERY"] * 5)
    with client_for(llm, FakeGraphRepository(), chat_rate_limit_requests=2) as client:
        codes = [client.post("/api/v1/chat", json={"question": "hi"}).status_code for _ in range(3)]
        blocked = client.post("/api/v1/chat", json={"question": "hi"})
    assert codes == [200, 200, 429]
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert int(blocked.headers["Retry-After"]) > 0


def test_llm_outage_maps_to_503():
    with client_for(FakeLanguageModel([LanguageModelError("down")]), FakeGraphRepository()) as client:
        response = client.post("/api/v1/chat", json={"question": "hi"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "llm_unavailable"
    assert "down" not in response.text  # internal details are not leaked


def test_llm_quota_exhaustion_maps_to_busy_with_retry_after():
    with client_for(FakeLanguageModel([LanguageModelBusyError("429 quota")]), FakeGraphRepository()) as client:
        response = client.post("/api/v1/chat", json={"question": "hi"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "llm_busy"
    assert response.headers["Retry-After"] == "30"


def test_graph_outage_maps_to_503():
    llm = FakeLanguageModel(["MATCH (s:Skill) RETURN s"])
    with client_for(llm, FakeGraphRepository([GraphUnavailableError("conn refused")])) as client:
        response = client.post("/api/v1/chat", json={"question": "skills?"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "graph_unavailable"


def test_unknown_route_uses_error_envelope():
    with client_for(FakeLanguageModel([]), FakeGraphRepository()) as client:
        response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_cors_allows_configured_origin_only():
    with client_for(FakeLanguageModel([]), FakeGraphRepository()) as client:
        allowed = client.options(
            "/api/v1/chat",
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        denied = client.options(
            "/api/v1/chat",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == ORIGIN
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_openapi_documents_the_contract():
    with client_for(FakeLanguageModel([]), FakeGraphRepository()) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) >= {"/health", "/health/ready", "/api/v1/graph", "/api/v1/chat"}
