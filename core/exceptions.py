"""Custom exceptions for consistent API error handling."""


class ArtifactConflictError(Exception):
    """Raised when an artifact operation would violate immutability (e.g. save existing artifact)."""

    def __init__(self, message: str = "Artifacts are immutable. Update not allowed."):
        self.message = message
        super().__init__(self.message)
