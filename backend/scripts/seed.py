"""Load data/career_graph.json into Neo4j, replacing whatever is there.

    python -m scripts.seed              # validate and load
    python -m scripts.seed --dry-run    # validate only
    python -m scripts.seed --http       # load over HTTPS (Query API) when port 7687 is blocked

Uses the NEO4J_* settings from the environment / .env (no LLM key needed).
Needs a user with write access.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from neo4j import AsyncGraphDatabase

from app.config import Neo4jSettings
from app.domain.career_data import load_career_data
from app.domain.errors import InvalidCareerDataError
from app.infrastructure.neo4j_http_seeder import Neo4jHttpSeeder, query_api_base_url
from app.infrastructure.neo4j_seeder import Neo4jSeeder

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "career_graph.json"


async def seed(data_path: Path, dry_run: bool, http: bool = False) -> int:
    try:
        dataset = load_career_data(data_path)
    except InvalidCareerDataError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Valid dataset: {len(dataset.nodes)} nodes, {len(dataset.relationships)} relationships.")
    if dry_run:
        return 0

    settings = Neo4jSettings()  # type: ignore[call-arg]  # values come from the environment
    if http:
        base_url = query_api_base_url(settings.neo4j_uri)
        summary = await Neo4jHttpSeeder(
            base_url=base_url,
            database=settings.neo4j_database,
            user=settings.neo4j_user,
            password=settings.neo4j_password.get_secret_value(),
        ).replace_graph(dataset)
        print(
            f"Loaded {summary.nodes} nodes and {summary.relationships} relationships into {base_url} (HTTPS Query API)."
        )
        return 0

    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value())
    )
    try:
        summary = await Neo4jSeeder(driver, database=settings.neo4j_database).replace_graph(dataset)
    finally:
        await driver.close()
    print(f"Loaded {summary.nodes} nodes and {summary.relationships} relationships into {settings.neo4j_uri}.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--dry-run", action="store_true", help="validate the dataset without touching Neo4j")
    parser.add_argument("--http", action="store_true", help="load over the HTTPS Query API instead of Bolt")
    args = parser.parse_args()
    sys.exit(asyncio.run(seed(args.data, args.dry_run, args.http)))


if __name__ == "__main__":
    main()
