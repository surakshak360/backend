from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class JobCreate(BaseModel):
    file_id: Optional[str] = None
    service: Literal["scam-intelligence", "vision", "intelligence"]
    endpoint: str = Field(..., json_schema_extra={"example": "/audio"})
    input_data: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    job_id: str
    service: str
    endpoint: str
    input: Optional[Dict[str, Any]] = None
    status: Literal["queued", "processing", "completed", "failed"]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
