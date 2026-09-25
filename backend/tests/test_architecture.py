"""Enforce the layer rules so they can't erode silently.

domain          <- depends on nothing
services        <- domain
infrastructure  <- domain              (adapters implementing domain ports)
api             <- domain, services    (never infrastructure)
container/main  <- everything          (composition root)
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent / "app"

ALLOWED = {
    "domain": {"domain"},
    "services": {"domain", "services"},
    "infrastructure": {"domain", "infrastructure"},
    "api": {"domain", "services", "api"},
}


def app_imports(path: Path) -> set[str]:
    """Top-level app sub-packages imported by a module (e.g. {'domain', 'services'})."""
    imported: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        names = []
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        for name in names:
            parts = name.split(".")
            if parts[0] == "app" and len(parts) > 1:
                imported.add(parts[1])
    return imported


@pytest.mark.parametrize("layer", sorted(ALLOWED))
def test_layer_dependencies(layer):
    violations = {
        str(path.relative_to(APP)): sorted(app_imports(path) - ALLOWED[layer])
        for path in (APP / layer).rglob("*.py")
        if app_imports(path) - ALLOWED[layer]
    }
    assert violations == {}, f"{layer} imports outside its allowed layers: {violations}"


def test_domain_has_no_third_party_io_dependencies():
    forbidden = {"neo4j", "google", "fastapi", "starlette", "httpx"}
    for path in (APP / "domain").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        roots = {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {
            a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
        }
        assert not roots & forbidden, f"{path.name} imports {roots & forbidden}"
