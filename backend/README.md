# Career Graph API

Ask questions about Sanchit Kulkarni's career in plain English. The API turns each question into a **Cypher query**, runs it read-only against a **Neo4j knowledge graph** of roles, projects and skills, and answers **only from what the graph returns**. It also sends back the nodes and edges it touched, so a UI can highlight them.

```
"Which projects use LangGraph?"
        │
        ▼  Gemini: question → Cypher (schema-aware, few-shot)
MATCH (p:Project)-[u:USES]->(s:Skill) WHERE toLower(s.name) = 'langgraph' RETURN p, u, s
        │
        ▼  CypherGuard: read-only? known labels? LIMIT enforced?
        ▼  Neo4j: executed in a READ transaction with a timeout
rows + subgraph
        │
        ▼  Gemini: answer grounded in the rows only
{ "status": "answered", "answer": "Six projects use LangGraph: ...", "nodes": [...], "edges": [...] }
```

## Architecture

Clean layers with dependencies pointing inwards. `tests/test_architecture.py` enforces the import rules, so the boundaries can't erode silently.

```
app/
├── domain/            Pure Python. No I/O, no frameworks.
│   ├── models.py        Value objects: GraphNode, GraphEdge, Subgraph, SafeCypher, ChatAnswer
│   ├── schema.py        The graph schema: single source of truth for seed validation, guard and prompts
│   ├── ports.py         Interfaces: GraphRepository, LanguageModel
│   ├── career_data.py   Load + validate data/career_graph.json against the schema
│   └── errors.py
├── services/          Use cases. Depend on domain only (talk to the outside world through ports).
│   ├── chat_service.py  question → Cypher → guard → read → grounded answer (with one bounded repair)
│   ├── graph_service.py Full snapshot (TTL-cached) + readiness
│   ├── cypher_guard.py  Trust boundary for LLM-generated Cypher
│   └── prompts.py       Prompt templates + completion parsing
├── infrastructure/    Adapters implementing the ports.
│   ├── neo4j_repository.py  Read-only queries → domain models
│   ├── neo4j_seeder.py      Writes the dataset (used by scripts/seed.py only)
│   └── gemini_model.py      Google Gemini client
├── api/               HTTP only. Depends on services + domain, never infrastructure.
│   ├── routes.py, schemas.py (public DTOs), errors.py (error envelope),
│   ├── dependencies.py, rate_limit.py, state.py
├── container.py       Composition root: the one place adapters are chosen and wired
├── config.py          Settings from env
└── main.py            App factory
```

| Layer | May import |
|---|---|
| `domain` | nothing (stdlib only) |
| `services` | `domain` |
| `infrastructure` | `domain` |
| `api` | `domain`, `services` |
| `container`, `main` | everything |

Swapping Gemini for another LLM, or Neo4j for another graph store, means writing one new adapter and changing one line in `container.py`.

## External API (v1)

Interactive docs are served at `/docs` (OpenAPI at `/openapi.json`).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness, no dependencies checked. Use it to wake a sleeping instance. |
| `GET` | `/health/ready` | Readiness: `200 {"status":"ready","neo4j":"up"}` or `503` |
| `GET` | `/api/v1/graph` | Full graph snapshot for the initial render |
| `POST` | `/api/v1/chat` | Ask a question (rate-limited per client IP) |

### `POST /api/v1/chat`

Request (`question`: 1–300 chars, whitespace is normalised):

```json
{ "question": "What did you build at Evenflow?" }
```

Response `200`:

```json
{
  "status": "answered",
  "answer": "At Evenflow Brands, Sanchit built ...",
  "cypher": "MATCH (c:Company)<-[a:AT_COMPANY]-(r:Role)<-[b:BUILT_DURING]-(p:Project) ... LIMIT 50",
  "nodes": [{ "id": "evenflow-brands", "label": "Company", "name": "Evenflow Brands", "properties": { "industry": "B2B commerce" } }],
  "edges": [{ "id": "role-evenflow-AT_COMPANY-evenflow-brands", "source": "role-evenflow", "target": "evenflow-brands", "type": "AT_COMPANY" }]
}
```

`status` is one of the values below. Every status carries a human-readable `answer` a UI can show as-is.

| status | meaning |
|---|---|
| `answered` | Query ran and the answer is grounded in its rows |
| `no_results` | Valid query, nothing matched |
| `off_topic` | Not a question about Sanchit's career; the database was not queried |
| `refused` | The generated query failed the safety guard; nothing was executed |
| `failed` | The query errored (after one automatic repair attempt) or timed out |

### `GET /api/v1/graph`

```json
{ "nodes": [NodeOut, ...], "edges": [EdgeOut, ...] }
```

Node and edge ids are stable, so `/chat` results can be matched against the snapshot for highlighting.

### Errors

Every non-2xx response uses one envelope:

```json
{ "error": { "code": "rate_limited", "message": "Too many questions. Please wait a few minutes and try again." } }
```

| HTTP | code |
|---|---|
| 422 | `invalid_request` |
| 429 | `rate_limited` (with a `Retry-After` header) |
| 503 | `llm_busy` (Gemini quota/overload; `Retry-After: 30`), `llm_unavailable`, `graph_unavailable` |
| 404 / 405 | `not_found` / `method_not_allowed` |

## Safety model

The API runs LLM-written queries against a live database, so it has two independent safeguards:

1. **`CypherGuard`**. It lexes the query (comments stripped, string literals blanked) and rejects:
   - write, schema, admin and procedure clauses (`CREATE`, `MERGE`, `DELETE`, `SET`, `CALL`, `LOAD`, `FOREACH`, `UNION`, …)
   - namespaced functions (`apoc.*`, `db.*`)
   - multiple statements, parameters and backticks
   - labels and relationship types that aren't in the schema

   It also forces a final `LIMIT` of at most 50. Rejected queries are **not** sent back to the model for repair, so the model is never coached past the guard.
2. **Read-only transactions.** Every query runs with `RoutingControl.READ` and a timeout, so Neo4j itself rejects writes. An integration test bypasses the guard on purpose and checks that the database still refuses the write.

On top of that:
- Rate limiting per client IP (default 10 questions / 10 min).
- An in-memory answer cache (1 hour, 500 entries). Repeat questions, such as the suggested prompts, cost no LLM quota. Failed answers are never cached.
- A 300-character cap on questions.
- CORS restricted to known origins.
- The answer prompt treats query results as data, not instructions.
- Internal error details are logged, never returned to the client.

## The graph

`data/career_graph.json` is the source of truth. It's built from the resume and the project READMEs, and holds 94 nodes and 214 relationships:

```
(:Person)-[:HELD]->(:Role)-[:AT_COMPANY]->(:Company)
(:Person)-[:BUILT]->(:Project)-[:BUILT_DURING]->(:Role)
(:Project)-[:FOR_CLIENT]->(:Company)          (freelance work)
(:Project|Role)-[:USES]->(:Skill)
(:Person)-[:STUDIED_AT]->(:Education)
```

Tests enforce that every skill is backed by at least one project or role, and that every project is linked to Sanchit.

To change the graph: edit the JSON, run `python -m scripts.seed --dry-run` to validate it, then `python -m scripts.seed` to load it. The load replaces the database contents and is safe to re-run.

Can't run Python against the database, for example because a firewall blocks port 7687? Run `python -m scripts.export_cypher > seed.cypher` and paste the file into the Aura console's **Query** tab. An integration test checks that it builds exactly the same graph as `scripts.seed`.

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # fill in NEO4J_* and GOOGLE_API_KEY

python -m scripts.seed            # load the graph
uvicorn app.main:create_app --factory --reload --port 8000
```

```bash
curl localhost:8000/health/ready
curl -X POST localhost:8000/api/v1/chat -H 'content-type: application/json' \
  -d '{"question": "Which projects use LangGraph?"}'
```

For a local Neo4j, `docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5` works, or use a free AuraDB instance.

## Tests

```bash
pytest                                            # unit + API contract + architecture (no services needed)
NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=password pytest -m integration
ruff check . && ruff format --check .
```

⚠️ The integration tests **wipe** the target database. Point them at a throwaway instance, never at production.

Unit tests replace the two ports with in-memory fakes (`tests/fakes.py`). Integration tests use a real Neo4j with only the LLM scripted. They check that every few-shot prompt example runs against the real graph, so the examples can't rot.

## Deploy (Render)

`render.yaml` at the repo root is a Render Blueprint for this service.
1. Render → **New → Blueprint** → pick this repo.
2. Set the secrets: `NEO4J_URI`, `NEO4J_PASSWORD`, `GOOGLE_API_KEY`.
3. Set `ALLOWED_ORIGINS` to the portfolio's real URL.
4. Seed Aura once from your machine: `python -m scripts.seed`.

**LLM quota.** The default model is `gemini-3.5-flash-lite`, which allows 15 requests/min on Gemini's free tier. Each question costs 2 LLM calls, or 0 when it's served from cache, so that's roughly 7 new questions a minute across the whole site. `gemini-2.5-flash` only allows 5/min. For real traffic, enable billing on the Google AI project; paid-tier limits are far higher and flash-lite costs fractions of a cent per question. `GEMINI_MODEL` overrides the model.

Render's free tier sleeps after inactivity. A UI should call `/health` on page load to wake the service before the first question. The rate limiter is in-memory, which is fine on one instance; move it to Redis if you scale out.
