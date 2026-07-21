from typing import Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import get_mongo_db
from app.core.exceptions import APIException
from app.core.logging import logger


class CaseWorkflowService:
    @staticmethod
    async def create_case(reporter_id: str, case_data: dict) -> dict:
        db = get_mongo_db()
        now = datetime.now(timezone.utc)
        
        doc = {
            "reporter_id": ObjectId(reporter_id),
            "type": case_data.get("type", "other"),
            "status": "new",
            "priority": case_data.get("priority", "medium"),
            "source": case_data.get("source", "web"),
            "location": case_data.get("location"),
            "summary": case_data.get("summary", ""),
            "risk_score": 0.0,
            "assigned_officer": None,
            "created_at": now,
            "updated_at": now
        }
        
        if db is not None:
            res = await db.cases.insert_one(doc)
            doc["_id"] = res.inserted_id
        else:
            doc["_id"] = ObjectId()
            
        logger.info("Case created", case_id=str(doc["_id"]), reporter_id=reporter_id)
        return doc

    @staticmethod
    async def add_timeline_event(case_id: str, event_type: str, description: str, actor_id: Optional[str] = None):
        db = get_mongo_db()
        event = {
            "case_id": ObjectId(case_id),
            "event_type": event_type,
            "description": description,
            "actor_id": ObjectId(actor_id) if actor_id else None,
            "created_at": datetime.now(timezone.utc)
        }
        if db is not None:
            await db.case_timeline.insert_one(event)
