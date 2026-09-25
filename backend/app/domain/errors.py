"""Domain-level exceptions. Adapters translate library errors into these."""


class CareerGraphError(Exception):
    """Base class for all errors raised by this application."""


class UnsafeQueryError(CareerGraphError):
    """Generated Cypher failed the read-only / schema safety checks."""


class QueryExecutionError(CareerGraphError):
    """The database rejected a query (syntax error, type error, access mode...)."""


class QueryTimeoutError(QueryExecutionError):
    """The query exceeded the configured timeout."""


class GraphUnavailableError(CareerGraphError):
    """The graph database cannot be reached."""


class LanguageModelError(CareerGraphError):
    """The LLM provider failed or returned an unusable response."""


class InvalidCareerDataError(CareerGraphError):
    """Seed data does not conform to the graph schema."""
