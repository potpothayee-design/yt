"""Domain errors with clean HTTP mapping."""

from __future__ import annotations

from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application error."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppError):
    def __init__(self, what: str = "resource"):
        super().__init__(f"{what} not found", status.HTTP_404_NOT_FOUND)


class PermissionDeniedError(AppError):
    def __init__(self, detail: str = "permission denied"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    def __init__(self, detail: str = "conflict"):
        super().__init__(detail, status.HTTP_409_CONFLICT)


class ProviderNotConfiguredError(AppError):
    def __init__(self, capability: str, provider: str):
        super().__init__(
            f"Provider '{provider}' for capability '{capability}' is not configured. "
            "Add an API key on the API Keys page or switch to a local provider.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
