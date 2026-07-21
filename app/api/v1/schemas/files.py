from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PresignRequest(BaseModel):
    content_type: str = Field(..., json_schema_extra={"example": "audio/wav"})
    max_size_mb: int = Field(default=25, ge=1, le=100)
    purpose: str = Field(default="scam_analysis", json_schema_extra={"example": "scam_analysis"})
    original_name: Optional[str] = Field(default="upload.bin")


class PresignResponse(BaseModel):
    upload_url: str
    file_id: str
    expires_in: int = 300


class FileMetadataResponse(BaseModel):
    id: str
    file_id: str
    original_name: str
    mime_type: str
    size_bytes: int
    storage_url: str
    purpose: str
    uploaded_by: str
    expires_at: Optional[datetime] = None
    created_at: datetime
