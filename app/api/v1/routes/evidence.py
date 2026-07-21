from fastapi import APIRouter, Depends, Request, Query, status
from bson import ObjectId
from app.api.v1.schemas.envelope import make_envelope, make_paginated_envelope
from app.api.v1.deps import get_current_user
from app.core.database import get_mongo_db
from app.core.exceptions import APIException

router = APIRouter()


@router.get("/evidence", tags=["Evidence"])
async def list_evidence(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    evidence_type: str = Query(None, alias="type"),
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    query = {}
    if evidence_type:
        query["type"] = evidence_type

    evidence_list = []
    total = 0

    if db is not None:
        total = await db.evidence.count_documents(query)
        cursor = db.evidence.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
        async for ev in cursor:
            evidence_list.append({
                "id": str(ev["_id"]),
                "case_id": str(ev.get("case_id")),
                "type": ev.get("type"),
                "file_id": ev.get("file_id"),
                "ml_results": ev.get("ml_results"),
                "intelligence_output": ev.get("intelligence_output"),
                "created_at": ev.get("created_at")
            })
    else:
        evidence_list = [{
            "id": "65f1234567890abcdef12399",
            "case_id": "65f1234567890abcdef12346",
            "type": "audio",
            "file_id": "file_abc123",
            "ml_results": {"risk_score": 0.94},
            "created_at": "2026-07-21T10:00:00Z"
        }]
        total = 1

    return make_paginated_envelope(evidence_list, page, page_size, total, request_id=req_id)


@router.get("/evidence/{evidence_id}", tags=["Evidence"])
async def get_evidence(
    evidence_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    if db is not None:
        try:
            ev = await db.evidence.find_one({"_id": ObjectId(evidence_id)})
            if not ev:
                raise APIException("NOT_FOUND", "Evidence not found", status.HTTP_404_NOT_FOUND)
            
            ev_data = {
                "id": str(ev["_id"]),
                "case_id": str(ev.get("case_id")),
                "type": ev.get("type"),
                "file_id": ev.get("file_id"),
                "ml_results": ev.get("ml_results"),
                "intelligence_output": ev.get("intelligence_output"),
                "created_at": ev.get("created_at")
            }
            return make_envelope(ev_data, request_id=req_id)
        except Exception:
            raise APIException("NOT_FOUND", "Evidence not found", status.HTTP_404_NOT_FOUND)

    return make_envelope({
        "id": evidence_id,
        "case_id": "case_abc",
        "type": "audio",
        "file_id": "file_abc123",
        "ml_results": {"scam_intelligence": {"risk_score": 0.94}},
        "created_at": "2026-07-21T10:00:00Z"
    }, request_id=req_id)
