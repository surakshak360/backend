from typing import Dict, Any, Optional
from app.core.logging import logger
from app.services.websocket import ws_manager


class NotificationService:
    @staticmethod
    async def notify_case_update(case_id: str, changes: Dict[str, Any], user_id: Optional[str] = None):
        event_data = {
            "event": "case.updated",
            "data": {
                "case_id": case_id,
                "changes": changes
            }
        }
        logger.info("Dispatching notification for case update", case_id=case_id)
        if user_id:
            await ws_manager.send_personal_message(event_data, user_id)
        else:
            await ws_manager.broadcast("case.updated", event_data["data"])

    @staticmethod
    async def notify_job_completed(job_id: str, result: Dict[str, Any], user_id: Optional[str] = None):
        event_data = {
            "event": "job.completed",
            "data": {
                "job_id": job_id,
                "result": result
            }
        }
        logger.info("Dispatching notification for job completion", job_id=job_id)
        if user_id:
            await ws_manager.send_personal_message(event_data, user_id)
        else:
            await ws_manager.broadcast("job.completed", event_data["data"])
