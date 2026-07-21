from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from bson import ObjectId

from app.api.v1.schemas.cases import CaseCreate, CaseUpdate
from app.api.v1.schemas.evidence import EvidenceCreate
from app.api.v1.schemas.envelope import make_envelope, make_paginated_envelope
from app.api.v1.deps import get_current_user, get_ml_client_dep
from app.core.database import get_mongo_db
from app.core.exceptions import APIException
from app.services.notifications import NotificationService
from app.services.ml_client import MLClient

router = APIRouter()


@router.get("/cases", tags=["Cases"])
async def list_cases(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None, alias="type"),
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    if priority:
        query["priority"] = priority
    if case_type:
        query["type"] = case_type

    # Citizens only see their reported cases
    if current_user.get("role") == "citizen":
        query["reporter_id"] = ObjectId(current_user.get("id")) if ObjectId.is_valid(current_user.get("id")) else current_user.get("id")

    cases_list = []
    total = 0

    if db is not None:
        total = await db.cases.count_documents(query)
        cursor = db.cases.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
        async for c in cursor:
            cases_list.append({
                "id": str(c["_id"]),
                "reporter_id": str(c.get("reporter_id")),
                "type": c.get("type"),
                "status": c.get("status"),
                "priority": c.get("priority"),
                "source": c.get("source"),
                "location": c.get("location"),
                "summary": c.get("summary"),
                "risk_score": c.get("risk_score", 0.0),
                "assigned_officer": str(c["assigned_officer"]) if c.get("assigned_officer") else None,
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at")
            })
    else:
        # Fallback dummy list
        cases_list = [{
            "id": "65f1234567890abcdef12346",
            "reporter_id": str(current_user.get("id")),
            "type": "digital_arrest",
            "status": "new",
            "priority": "high",
            "source": "web",
            "summary": "Impersonation call claiming CBI warrant.",
            "risk_score": 0.92,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }]
        total = 1

    return make_paginated_envelope(cases_list, page, page_size, total, request_id=req_id)


@router.post("/cases", tags=["Cases"])
async def create_case(
    body: CaseCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    user_id = current_user.get("id")
    now = datetime.now(timezone.utc)
    
    case_doc = {
        "reporter_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
        "type": body.type,
        "status": "new",
        "priority": body.priority or "medium",
        "source": body.source or "web",
        "location": body.location.model_dump() if body.location else None,
        "summary": body.summary,
        "risk_score": 0.0,
        "assigned_officer": None,
        "created_at": now,
        "updated_at": now
    }

    if db is not None:
        res = await db.cases.insert_one(case_doc)
        case_id = str(res.inserted_id)
    else:
        case_id = f"case_{ObjectId()}"

    case_data = {
        "id": case_id,
        "reporter_id": user_id,
        "type": body.type,
        "status": "new",
        "priority": body.priority or "medium",
        "source": body.source or "web",
        "summary": body.summary,
        "risk_score": 0.0,
        "created_at": now,
        "updated_at": now
    }

    await NotificationService.notify_case_update(case_id, {"status": "created"}, user_id)
    return make_envelope(case_data, request_id=req_id)


@router.get("/cases/{case_id}", tags=["Cases"])
async def get_case(
    case_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    if db is not None:
        try:
            c = await db.cases.find_one({"_id": ObjectId(case_id)})
            if not c:
                raise APIException("NOT_FOUND", "Case not found", status.HTTP_404_NOT_FOUND)
            
            case_data = {
                "id": str(c["_id"]),
                "reporter_id": str(c.get("reporter_id")),
                "type": c.get("type"),
                "status": c.get("status"),
                "priority": c.get("priority"),
                "source": c.get("source"),
                "location": c.get("location"),
                "summary": c.get("summary"),
                "risk_score": c.get("risk_score", 0.0),
                "assigned_officer": str(c["assigned_officer"]) if c.get("assigned_officer") else None,
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at")
            }
            return make_envelope(case_data, request_id=req_id)
        except Exception:
            raise APIException("NOT_FOUND", "Case not found", status.HTTP_404_NOT_FOUND)

    return make_envelope({
        "id": case_id,
        "reporter_id": current_user.get("id"),
        "type": "digital_arrest",
        "status": "new",
        "priority": "high",
        "source": "web",
        "summary": "Sample digital arrest case summary.",
        "risk_score": 0.94,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }, request_id=req_id)


@router.patch("/cases/{case_id}", tags=["Cases"])
async def update_case(
    case_id: str,
    body: CaseUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)

    if "assigned_officer" in update_data and update_data["assigned_officer"] and ObjectId.is_valid(update_data["assigned_officer"]):
        update_data["assigned_officer"] = ObjectId(update_data["assigned_officer"])

    if db is not None:
        try:
            res = await db.cases.update_one({"_id": ObjectId(case_id)}, {"$set": update_data})
            if res.matched_count == 0:
                raise APIException("NOT_FOUND", "Case not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            raise APIException("NOT_FOUND", f"Case update failed: {str(e)}", status.HTTP_404_NOT_FOUND)

    await NotificationService.notify_case_update(case_id, update_data)
    return make_envelope({"id": case_id, "updated": True, "changes": update_data}, request_id=req_id)


@router.delete("/cases/{case_id}", tags=["Cases"])
async def delete_case(
    case_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    if db is not None:
        try:
            res = await db.cases.delete_one({"_id": ObjectId(case_id)})
            if res.deleted_count == 0:
                raise APIException("NOT_FOUND", "Case not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            raise APIException("NOT_FOUND", f"Case deletion failed: {str(e)}", status.HTTP_404_NOT_FOUND)

    return make_envelope({"id": case_id, "deleted": True}, request_id=req_id)


@router.get("/cases/{case_id}/evidence", tags=["Cases"])
async def get_case_evidence(
    case_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    evidence_list = []
    if db is not None:
        try:
            cursor = db.evidence.find({"case_id": ObjectId(case_id)})
            async for ev in cursor:
                evidence_list.append({
                    "id": str(ev["_id"]),
                    "case_id": str(ev["case_id"]),
                    "type": ev.get("type"),
                    "file_id": ev.get("file_id"),
                    "ml_results": ev.get("ml_results"),
                    "intelligence_output": ev.get("intelligence_output"),
                    "created_at": ev.get("created_at")
                })
        except Exception:
            pass

    return make_envelope(evidence_list, request_id=req_id)


@router.post("/cases/{case_id}/evidence", tags=["Cases"])
async def add_case_evidence(
    case_id: str,
    body: EvidenceCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    ml_client: MLClient = Depends(get_ml_client_dep)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    now = datetime.now(timezone.utc)
    ml_res = {}
    if body.type == "audio" and body.file_id:
        ml_res = await ml_client.analyze_audio(body.file_id)
    elif body.type == "text" and body.text_content:
        ml_res = await ml_client.analyze_text(body.text_content)
    elif body.type == "image" and body.file_id:
        ml_res = await ml_client.analyze_image(body.file_id)

    intel_res = await ml_client.fuse_intelligence(case_id, scam_result=ml_res)

    evidence_doc = {
        "case_id": ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id,
        "type": body.type,
        "file_id": body.file_id,
        "ml_results": {"scam_intelligence": ml_res},
        "intelligence_output": intel_res,
        "created_at": now
    }

    if db is not None:
        res = await db.evidence.insert_one(evidence_doc)
        ev_id = str(res.inserted_id)
        # Update case risk score if available from fusion
        risk_score = intel_res.get("overall_score", ml_res.get("risk_score", 0.85))
        await db.cases.update_one({"_id": ObjectId(case_id)}, {"$set": {"risk_score": risk_score, "updated_at": now}})
    else:
        ev_id = f"ev_{ObjectId()}"

    evidence_doc["id"] = ev_id
    evidence_doc["case_id"] = case_id

    return make_envelope(evidence_doc, request_id=req_id)


@router.get("/cases/{case_id}/timeline", tags=["Cases"])
async def get_case_timeline(
    case_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    timeline = []
    if db is not None:
        try:
            cursor = db.case_timeline.find({"case_id": ObjectId(case_id)}).sort("created_at", 1)
            async for t in cursor:
                timeline.append({
                    "id": str(t["_id"]),
                    "case_id": str(t["case_id"]),
                    "event_type": t.get("event_type"),
                    "description": t.get("description"),
                    "created_at": t.get("created_at")
                })
        except Exception:
            pass

    if not timeline:
        timeline = [{
            "event_type": "case_created",
            "description": "Case reported by user",
            "created_at": datetime.now(timezone.utc)
        }]

    return make_envelope(timeline, request_id=req_id)
