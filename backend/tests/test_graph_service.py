from app.domain.models import GraphNode, Subgraph
from app.services.graph_service import GraphService
from tests.fakes import FakeGraphRepository

SNAPSHOT = Subgraph((GraphNode("sanchit", "Person", "Sanchit Kulkarni"),))


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


async def test_snapshot_is_cached_until_ttl_expires():
    repo = FakeGraphRepository(snapshot=SNAPSHOT)
    clock = Clock()
    service = GraphService(repo, snapshot_ttl_seconds=60, clock=clock)

    assert await service.snapshot() == SNAPSHOT
    clock.now = 59
    await service.snapshot()
    assert repo.snapshot_calls == 1

    clock.now = 60
    await service.snapshot()
    assert repo.snapshot_calls == 2


async def test_readiness_reflects_repository():
    assert await GraphService(FakeGraphRepository(ready=True), snapshot_ttl_seconds=1).is_ready()
    assert not await GraphService(FakeGraphRepository(ready=False), snapshot_ttl_seconds=1).is_ready()
