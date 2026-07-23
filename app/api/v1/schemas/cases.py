from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime


class GeoLocation(BaseModel):
    type: Optional[str] = "Point"
    coordinates: Optional[List[float]] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    district: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None


class CaseCreate(BaseModel):
    type: str = Field(..., description="Type of incident e.g. digital_arrest, counterfeit, scam, identity, phishing, other")
    summary: str
    priority: Optional[str] = "medium"
    source: Optional[str] = "web"
    location: Optional[GeoLocation] = None
    reporter_phone: Optional[str] = None


class CaseUpdate(BaseModel):
    type: Optional[Literal["digital_arrest", "counterfeit", "phishing", "other"]] = None
    status: Optional[Literal["new", "triaged", "investigating", "resolved", "closed"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    assigned_officer: Optional[str] = None
    summary: Optional[str] = None
    risk_score: Optional[float] = None


class CaseResponse(BaseModel):
    id: str
    reporter_id: str
    type: Literal["digital_arrest", "counterfeit", "phishing", "other"]
    status: Literal["new", "triaged", "investigating", "resolved", "closed"]
    priority: Literal["low", "medium", "high", "critical"]
    source: Literal["whatsapp", "web", "call", "app"]
    location: Optional[GeoLocation] = None
    summary: str
    risk_score: float = 0.0
    assigned_officer: Optional[str] = None
    created_at: datetime
    updated_at: datetime
