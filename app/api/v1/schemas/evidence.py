from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class EvidenceCreate(BaseModel):
    case_id: str
    type: Literal["audio", "image", "document", "url", "text"]
    file_id: Optional[str] = None
    text_content: Optional[str] = None
    url: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: str
    case_id: str
    type: Literal["audio", "image", "document", "url", "text"]
    file_id: Optional[str] = None
    ml_results: Optional[Dict[str, Any]] = None
    intelligence_output: Optional[Dict[str, Any]] = None
    created_at: datetime
