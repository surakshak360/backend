from typing import Generator, Optional
from fastapi import Depends, Header, HTTPException, status
from bson import ObjectId
from app.core.security import decode_token
from app.core.database import get_mongo_db
from app.core.exceptions import APIException
from app.services.ml_client import MLClient


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise APIException("UNAUTHORIZED", "Missing or invalid authorization header", status.HTTP_401_UNAUTHORIZED)
    
    token = authorization.replace("Bearer ", "").strip()
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise APIException("UNAUTHORIZED", f"Invalid token: {str(e)}", status.HTTP_401_UNAUTHORIZED)
    
    user_id = payload.get("sub")
    if not user_id:
        raise APIException("UNAUTHORIZED", "Token missing subject claim", status.HTTP_401_UNAUTHORIZED)
    
    db = get_mongo_db()
    if db is not None:
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                return user
        except Exception:
            pass
            
    # Mock user fallback for testing/in-memory mode if DB not populated
    return {
        "id": user_id,
        "_id": user_id,
        "phone": "+919876543210",
        "email": "user@example.com",
        "role": payload.get("roles", ["citizen"])[0] if payload.get("roles") else "citizen",
        "language": "en",
        "is_verified": True
    }


def require_roles(allowed_roles: list):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "citizen")
        if user_role not in allowed_roles:
            raise APIException("FORBIDDEN", f"Role '{user_role}' is not authorized for this operation", status.HTTP_403_FORBIDDEN)
        return current_user
    return role_checker


async def get_ml_client_dep() -> Generator:
    client = MLClient()
    try:
        yield client
    finally:
        await client.close()
