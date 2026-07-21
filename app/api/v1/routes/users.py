from fastapi import APIRouter, Depends, Request, Query, status
from bson import ObjectId
from app.api.v1.schemas.envelope import make_envelope, make_paginated_envelope
from app.api.v1.schemas.users import UserUpdate
from app.api.v1.deps import get_current_user, require_roles
from app.core.database import get_mongo_db
from app.core.exceptions import APIException

router = APIRouter()


@router.get("/users", tags=["Users"])
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str = Query(None),
    current_user: dict = Depends(require_roles(["admin", "officer"]))
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    query = {}
    if role:
        query["role"] = role

    users_list = []
    total = 0
    
    if db is not None:
        total = await db.users.count_documents(query)
        cursor = db.users.find(query).skip((page - 1) * page_size).limit(page_size)
        async for u in cursor:
            users_list.append({
                "id": str(u["_id"]),
                "phone": u.get("phone"),
                "email": u.get("email"),
                "role": u.get("role"),
                "language": u.get("language", "en"),
                "is_verified": u.get("is_verified", True),
                "created_at": u.get("created_at")
            })
    else:
        # Fallback dummy list
        users_list = [{
            "id": "65f1234567890abcdef12345",
            "phone": "+919876543210",
            "email": "user@example.com",
            "role": "citizen",
            "language": "en",
            "is_verified": True
        }]
        total = 1

    return make_paginated_envelope(users_list, page, page_size, total, request_id=req_id)


@router.get("/users/{user_id}", tags=["Users"])
async def get_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    if db is not None:
        try:
            u = await db.users.find_one({"_id": ObjectId(user_id)})
            if not u:
                raise APIException("NOT_FOUND", "User not found", status.HTTP_404_NOT_FOUND)
            user_data = {
                "id": str(u["_id"]),
                "phone": u.get("phone"),
                "email": u.get("email"),
                "role": u.get("role"),
                "language": u.get("language", "en"),
                "is_verified": u.get("is_verified", True)
            }
            return make_envelope(user_data, request_id=req_id)
        except Exception:
            raise APIException("NOT_FOUND", "User not found", status.HTTP_404_NOT_FOUND)
            
    return make_envelope({
        "id": user_id,
        "phone": "+919876543210",
        "email": "user@example.com",
        "role": "citizen",
        "language": "en",
        "is_verified": True
    }, request_id=req_id)


@router.patch("/users/{user_id}", tags=["Users"])
async def update_user(
    user_id: str,
    body: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    
    if db is not None:
        try:
            res = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
            if res.matched_count == 0:
                raise APIException("NOT_FOUND", "User not found", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            raise APIException("NOT_FOUND", f"Update failed: {str(e)}", status.HTTP_404_NOT_FOUND)

    return make_envelope({"id": user_id, "updated": True, "changes": update_data}, request_id=req_id)
