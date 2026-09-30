"""Recoverable protocol errors raised by the test engine."""


class TestFlowError(Exception):
    """A recoverable protocol violation (maps to 409/410 by the API layer)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class NotFoundError(Exception):
    pass
