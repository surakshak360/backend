from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request, status
from bson import ObjectId
from app.api.v1.schemas.files import PresignRequest
from app.api.v1.schemas.envelope import make_envelope
from app.api.v1.deps import get_current_user
from app.services.file_storage import FileStorageService
from app.core.database import get_mongo_db
from app.core.exceptions import APIException

router = APIRouter()


@router.post("/upload/presign", tags=["Files"])
async def get_presigned_url(
    body: PresignRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    user_id = current_user.get("id")
    
    if body.max_size_mb > 100:
        raise APIException("VALIDATION_ERROR", "Maximum allowed file size is 100 MB", status.HTTP_400_BAD_REQUEST)

    presign_info = FileStorageService.generate_presigned_upload_url(
        content_type=body.content_type,
        purpose=body.purpose,
        max_size_mb=body.max_size_mb,
        original_name=body.original_name or "file.bin"
    )

    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    file_doc = {
        "file_id": presign_info["file_id"],
        "original_name": presign_info["original_name"],
        "mime_type": body.content_type,
        "size_bytes": 0,
        "storage_url": presign_info["upload_url"],
        "purpose": body.purpose,
        "uploaded_by": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
        "expires_at": now + timedelta(days=30),
        "created_at": now
    }

    if db is not None:
        await db.files.insert_one(file_doc)

    return make_envelope({
        "upload_url": presign_info["upload_url"],
        "file_id": presign_info["file_id"],
        "expires_in": presign_info["expires_in"]
    }, request_id=req_id)


@router.get("/files/{file_id}", tags=["Files"])
async def get_file_metadata(
    file_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    if db is not None:
        file_doc = await db.files.find_one({"file_id": file_id})
        if file_doc:
            return make_envelope({
                "id": str(file_doc["_id"]),
                "file_id": file_doc["file_id"],
                "original_name": file_doc["original_name"],
                "mime_type": file_doc["mime_type"],
                "storage_url": file_doc["storage_url"],
                "purpose": file_doc["purpose"],
                "created_at": file_doc["created_at"]
            }, request_id=req_id)

    return make_envelope({
        "id": "65f1234567890abcdef12388",
        "file_id": file_id,
        "original_name": "audio_sample.wav",
        "mime_type": "audio/wav",
        "storage_url": f"https://res.cloudinary.com/demo/raw/upload/{file_id}.wav",
        "purpose": "scam_analysis",
        "created_at": datetime.now(timezone.utc)
    }, request_id=req_id)
