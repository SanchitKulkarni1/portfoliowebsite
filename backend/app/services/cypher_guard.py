"""Validate LLM-generated Cypher before it reaches the database.

This is the trust boundary between untrusted model output and the graph. It is
one of two independent safeguards: the repository also executes every query in a
read-only transaction, so a write that slipped past this guard would still fail.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain import schema
from app.domain.errors import UnsafeQueryError
from app.domain.models import SafeCypher

# Clauses that write data, touch the schema/admin surface, call procedures or
# combine result sets in ways that defeat LIMIT enforcement.
FORBIDDEN_KEYWORDS = (
    "CREATE",
    "MERGE",
    "DELETE",
    "DETACH",
    "SET",
    "REMOVE",
    "DROP",
    "INSERT",
    "LOAD",
    "CALL",
    "FOREACH",
    "USE",
    "UNION",
    "GRANT",
    "DENY",
    "REVOKE",
    "ALTER",
    "RENAME",
    "TERMINATE",
    "SHOW",
)
_FORBIDDEN = re.compile(r"(?<![\w.$])(" + "|".join(FORBIDDEN_KEYWORDS) + r")(?![\w])", re.IGNORECASE)
# Namespaced function calls (apoc.*, db.*, dbms.*...) can run arbitrary Cypher or reach the admin surface.
_NAMESPACED_CALL = re.compile(r"(?<![\w.])[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\s*\(")
_ALLOWED_START = re.compile(r"^(OPTIONAL\s+MATCH|MATCH|WITH|UNWIND|RETURN)\b", re.IGNORECASE)
_HAS_RETURN = re.compile(r"(?<![\w.])RETURN(?![\w])", re.IGNORECASE)
_NODE_LABELS = re.compile(r"\(\s*(?:[A-Za-z_]\w*)?\s*:\s*([A-Za-z_]\w*(?:\s*[:|&]\s*!?\s*[A-Za-z_]\w*)*)")
_REL_TYPES = re.compile(r"\[\s*(?:[A-Za-z_]\w*)?\s*:\s*!?\s*([A-Za-z_]\w*(?:\s*\|\s*:?\s*[A-Za-z_]\w*)*)")
_NAME_SPLIT = re.compile(r"[\s:|&!]+")
_TRAILING_LIMIT = re.compile(r"\bLIMIT\s+(\d+)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class _Lexed:
    code: str  # the query with comments removed (string literals intact)
    scan: str  # the same query with string literal contents blanked, for keyword scanning


def _lex(query: str) -> _Lexed:
    """Strip comments and blank out string literals, respecting quotes and escapes."""
    code: list[str] = []
    scan: list[str] = []
    i, n = 0, len(query)
    while i < n:
        ch = query[i]
        if ch in ("'", '"'):
            end = i + 1
            while end < n and query[end] != ch:
                end += 2 if query[end] == "\\" else 1
            if end >= n:
                raise UnsafeQueryError("Unterminated string literal.")
            code.append(query[i : end + 1])
            scan.append(ch + ch)
            i = end + 1
        elif query.startswith("//", i):
            newline = query.find("\n", i)
            i = n if newline == -1 else newline
        elif query.startswith("/*", i):
            close = query.find("*/", i + 2)
            if close == -1:
                raise UnsafeQueryError("Unterminated comment.")
            code.append(" ")
            scan.append(" ")
            i = close + 2
        else:
            code.append(ch)
            scan.append(ch)
            i += 1
    return _Lexed("".join(code).strip(), "".join(scan).strip())


class CypherGuard:
    def __init__(self, *, max_rows: int) -> None:
        if max_rows < 1:
            raise ValueError("max_rows must be positive")
        self._max_rows = max_rows

    def validate(self, query: str) -> SafeCypher:
        """Return a SafeCypher, or raise UnsafeQueryError explaining why the query was rejected."""
        lexed = _lex(query.strip().rstrip(";").strip())
        code, scan = lexed.code, lexed.scan

        if not code:
            raise UnsafeQueryError("Empty query.")
        if ";" in scan:
            raise UnsafeQueryError("Multiple statements are not allowed.")
        if "`" in scan:
            raise UnsafeQueryError("Backtick-quoted identifiers are not allowed.")
        if "$" in scan:
            raise UnsafeQueryError("Query parameters are not allowed.")
        forbidden = _FORBIDDEN.search(scan)
        if forbidden:
            raise UnsafeQueryError(f"Forbidden clause: {forbidden.group(1).upper()}.")
        if _NAMESPACED_CALL.search(scan):
            raise UnsafeQueryError("Namespaced function calls are not allowed.")
        if not _ALLOWED_START.match(scan):
            raise UnsafeQueryError("Query must start with MATCH, OPTIONAL MATCH, WITH, UNWIND or RETURN.")
        if not _HAS_RETURN.search(scan):
            raise UnsafeQueryError("Query must RETURN something.")
        self._check_schema_names(scan)

        return SafeCypher(self._enforce_limit(code))

    def _check_schema_names(self, scan: str) -> None:
        for match in _NODE_LABELS.finditer(scan):
            for label in filter(None, _NAME_SPLIT.split(match.group(1))):
                if label not in schema.NODE_LABELS:
                    raise UnsafeQueryError(f"Unknown node label: {label}.")
        for match in _REL_TYPES.finditer(scan):
            for rel_type in filter(None, _NAME_SPLIT.split(match.group(1))):
                if rel_type not in schema.RELATIONSHIP_NAMES:
                    raise UnsafeQueryError(f"Unknown relationship type: {rel_type}.")

    def _enforce_limit(self, code: str) -> str:
        trailing = _TRAILING_LIMIT.search(code)
        if trailing is None:
            return f"{code}\nLIMIT {self._max_rows}"
        if int(trailing.group(1)) > self._max_rows:
            return code[: trailing.start()] + f"LIMIT {self._max_rows}"
        return code
