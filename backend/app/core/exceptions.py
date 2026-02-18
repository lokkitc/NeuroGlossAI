from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class NeuroGlossException(HTTPException):
    """Базовое исключение для NeuroGlossAI"""
    def __init__(
        self,
        status_code: int,
        code: str | None = None,
        detail: Any = None,
        details: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.code = code or "neurogloss_error"
        self.details = details
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class EntityNotFoundException(NeuroGlossException):
    def __init__(self, entity_name: str, entity_id: Any = None):
        detail = f"{entity_name} not found"
        if entity_id:
            detail += f" with id {entity_id}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, code="not_found", detail=detail)

class ServiceException(NeuroGlossException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="service_unavailable", detail=message)

class RateLimitExceededException(NeuroGlossException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, code="rate_limited", detail=detail)
