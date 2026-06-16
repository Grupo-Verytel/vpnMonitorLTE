"""Custom application exceptions."""


class FortiGateAPIError(Exception):
    """Raised when the FortiGate REST API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class SnapshotError(Exception):
    """Raised when snapshot processing fails unexpectedly."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
