import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.core.config import settings


class FileStorageService:
    @staticmethod
    def generate_presigned_upload_url(
        content_type: str,
        purpose: str = "scam_analysis",
        max_size_mb: int = 25,
        original_name: str = "file.bin"
    ) -> Dict[str, Any]:
        file_id = f"file_{uuid.uuid4().hex[:12]}"
        
        # In production Cloudinary or AWS S3 presigned URL is returned
        upload_url = f"https://api.cloudinary.com/v1_1/surakshak360/upload?file_id={file_id}"
        
        return {
            "upload_url": upload_url,
            "file_id": file_id,
            "expires_in": 300,
            "original_name": original_name,
            "mime_type": content_type,
            "purpose": purpose,
            "size_limit_bytes": max_size_mb * 1024 * 1024
        }
