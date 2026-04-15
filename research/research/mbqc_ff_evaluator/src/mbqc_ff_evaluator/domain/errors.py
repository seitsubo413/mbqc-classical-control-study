"""Domain-specific errors."""


class MBQCFFEvaluatorError(Exception):
    """Base exception for the project."""


class DependencyGraphError(MBQCFFEvaluatorError):
    """Raised when the dependency graph is malformed."""
