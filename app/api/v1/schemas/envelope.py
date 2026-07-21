from typing import Generic, Optional, TypeVar, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")


class MetaEnvelope(BaseModel):
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0.0"


class PaginationMetaEnvelope(MetaEnvelope):
    page: int
    page_size: int
    total: int
    total_pages: int


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: MetaEnvelope


class PaginatedResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: PaginationMetaEnvelope


class ErrorDetailEnvelope(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: str


class ErrorResponseEnvelope(BaseModel):
    success: bool = False
    error: ErrorDetailEnvelope


def make_envelope(data: Any, request_id: str = "req_default") -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    }


def make_paginated_envelope(
    data: Any,
    page: int,
    page_size: int,
    total: int,
    request_id: str = "req_default"
) -> Dict[str, Any]:
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "success": True,
        "data": data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    }
