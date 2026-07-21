import asyncio
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "surakshak360",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_evidence_task(self, evidence_id: str, case_id: str, file_id: str, evidence_type: str):
    from app.services.ml_client import MLClient

    async def _async_process():
        ml = MLClient()
        try:
            if evidence_type == "audio":
                result = await ml.analyze_audio(file_id)
            elif evidence_type == "image":
                result = await ml.analyze_image(file_id)
            else:
                result = {"processed": True}

            await ml.fuse_intelligence(case_id, scam_result=result)
            return result
        finally:
            await ml.close()

    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(_async_process())
    else:
        return asyncio.run(_async_process())
