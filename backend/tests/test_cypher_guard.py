import pytest

from app.domain.errors import UnsafeQueryError
from app.services.cypher_guard import CypherGuard
from app.services.prompts import FEW_SHOT_EXAMPLES

guard = CypherGuard(max_rows=50)


@pytest.mark.parametrize(
    "query",
    [
        "MATCH (p:Project)-[u:USES]->(s:Skill) WHERE toLower(s.name) = 'langgraph' RETURN p, u, s",
        "OPTIONAL MATCH (r:Role) RETURN r",
        "MATCH (me:Person {id: 'sanchit'})-[:HELD]->(r:Role) RETURN r ORDER BY r.start DESC",
        "MATCH (s:Skill)<-[u:USES]-(x) WITH s, count(u) AS usage ORDER BY usage DESC RETURN s, usage",
        "MATCH p = (:Person)-[:BUILT|HELD*1..2]-(n) RETURN p",
        "MATCH (p:Project) WHERE p.summary CONTAINS 'delete manual work; create value' RETURN p",
        "MATCH (p:Project) WHERE p.repo_url STARTS WITH 'https://github.com' RETURN p",
        "MATCH (r:Role) WITH r, r.start AS start RETURN r, start",
        "MATCH (n) WHERE n:Project OR n:Skill RETURN n",
    ],
)
def test_accepts_read_only_queries(query):
    assert guard.validate(query).text.startswith(query.split()[0])


@pytest.mark.parametrize("_question,query", FEW_SHOT_EXAMPLES)
def test_few_shot_examples_pass_the_guard(_question, query):
    guard.validate(query)


@pytest.mark.parametrize(
    "query,reason",
    [
        ("MATCH (n) DETACH DELETE n", "DETACH"),
        ("MATCH (n) DELETE n RETURN n", "DELETE"),
        ("CREATE (n:Skill {id: 'x'}) RETURN n", "CREATE"),
        ("MATCH (n:Skill) SET n.name = 'x' RETURN n", "SET"),
        ("MATCH (n:Skill) REMOVE n.name RETURN n", "REMOVE"),
        ("MATCH (a:Skill) MERGE (a)-[:USES]->(a) RETURN a", "MERGE"),
        ("MATCH (n) CALL db.labels() YIELD label RETURN label", "CALL"),
        ("MATCH (n) RETURN apoc.cypher.runFirstColumnSingle('MATCH (m) DETACH DELETE m', {})", "Namespaced"),
        ("LOAD CSV FROM 'http://x' AS row RETURN row", "LOAD"),
        ("MATCH (n) FOREACH (x IN [1] | SET n.a = 1) RETURN n", "FOREACH"),
        ("MATCH (n) RETURN n UNION MATCH (m) RETURN m", "UNION"),
        ("MATCH (n) RETURN n; MATCH (m) DETACH DELETE m", "Multiple statements"),
        ("MATCH (n) WHERE n.id = $id RETURN n", "parameters"),
        ("MATCH (n:`Project`) RETURN n", "Backtick"),
        ("MATCH (n:Secret) RETURN n", "Unknown node label"),
        ("MATCH (a)-[:KNOWS]->(b) RETURN a", "Unknown relationship type"),
        ("MATCH (n:Skill) RETURN n /* sneaky */ ; MATCH (m) DELETE m", "Multiple statements"),
        ("MATCH (n) // comment\nDETACH DELETE n", "DETACH"),
        ("MATCH (n) WHERE n.name = 'unterminated RETURN n", "Unterminated"),
        ("MATCH (n:Skill)", "must RETURN"),
        ("USE system SHOW USERS", "USE"),
        ("", "Empty"),
        ("WHERE true RETURN 1", "must start"),
    ],
)
def test_rejects_unsafe_queries(query, reason):
    with pytest.raises(UnsafeQueryError, match=reason):
        guard.validate(query)


def test_appends_limit_when_missing():
    assert guard.validate("MATCH (s:Skill) RETURN s").text.endswith("\nLIMIT 50")


def test_clamps_excessive_limit():
    assert guard.validate("MATCH (s:Skill) RETURN s LIMIT 100000").text.endswith("LIMIT 50")


def test_keeps_smaller_limit():
    assert guard.validate("MATCH (s:Skill) RETURN s LIMIT 5").text == "MATCH (s:Skill) RETURN s LIMIT 5"


def test_inner_limit_does_not_count_as_final_limit():
    query = "MATCH (s:Skill) WITH s LIMIT 5 MATCH (s)<-[:USES]-(p) RETURN s, p"
    assert guard.validate(query).text.endswith("\nLIMIT 50")


def test_strips_comments_and_trailing_semicolon_but_keeps_urls_in_strings():
    safe = guard.validate("MATCH (p:Project) // find it\nWHERE p.repo_url = 'https://github.com/x' RETURN p;")
    assert "find it" not in safe.text
    assert "'https://github.com/x'" in safe.text
    assert ";" not in safe.text
