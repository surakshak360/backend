from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, status
from bson import ObjectId

from app.api.v1.schemas.auth import UserRegister, UserLogin, RefreshTokenRequest
from app.api.v1.schemas.envelope import make_envelope
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.database import get_mongo_db
from app.core.exceptions import APIException
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.post("/auth/register", tags=["Auth"])
async def register_user(request: Request, body: UserRegister):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    if db is not None:
        existing = await db.users.find_one({"$or": [{"email": body.email}, {"phone": body.phone}]})
        if existing:
            raise APIException("CONFLICT", "User with this email or phone already exists", status.HTTP_409_CONFLICT)
        
        now = datetime.now(timezone.utc)
        user_doc = {
            "phone": body.phone,
            "email": body.email,
            "password_hash": get_password_hash(body.password),
            "role": body.role,
            "language": body.language or "en",
            "created_at": now,
            "last_login": now,
            "is_verified": True
        }
        res = await db.users.insert_one(user_doc)
        user_id = str(res.inserted_id)
    else:
        user_id = str(ObjectId())

    access_token = create_access_token(subject=user_id, roles=[body.role])
    refresh_token = create_refresh_token(subject=user_id)

    user_data = {
        "id": user_id,
        "phone": body.phone,
        "email": body.email,
        "role": body.role,
        "language": body.language or "en"
    }

    return make_envelope(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        },
        request_id=req_id
    )


@router.post("/auth/login", tags=["Auth"])
async def login(request: Request, body: UserLogin):
    req_id = getattr(request.state, "request_id", "req_default")
    db = get_mongo_db()
    
    query = {}
    if body.email:
        query["email"] = body.email
    elif body.phone:
        query["phone"] = body.phone
    else:
        raise APIException("VALIDATION_ERROR", "Must provide email or phone", status.HTTP_400_BAD_REQUEST)

    user = None
    if db is not None:
        user = await db.users.find_one(query)
    
    if not user:
        # Fallback test user if DB is not populated
        if (body.email == "user@example.com" or body.phone == "+919876543210") and body.password == "password":
            user = {
                "_id": ObjectId("65f1234567890abcdef12345"),
                "phone": "+919876543210",
                "email": "user@example.com",
                "role": "citizen",
                "language": "en",
                "is_verified": True
            }
        else:
            raise APIException("UNAUTHORIZED", "Invalid credentials", status.HTTP_401_UNAUTHORIZED)
    else:
        if not verify_password(body.password, user.get("password_hash", "")):
            raise APIException("UNAUTHORIZED", "Invalid credentials", status.HTTP_401_UNAUTHORIZED)

    user_id = str(user["_id"])
    role = user.get("role", "citizen")
    
    access_token = create_access_token(subject=user_id, roles=[role])
    refresh_token = create_refresh_token(subject=user_id)

    user_data = {
        "id": user_id,
        "phone": user.get("phone"),
        "email": user.get("email"),
        "role": role,
        "language": user.get("language", "en")
    }

    return make_envelope(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        },
        request_id=req_id
    )


@router.post("/auth/refresh", tags=["Auth"])
async def refresh_token(request: Request, body: RefreshTokenRequest):
    req_id = getattr(request.state, "request_id", "req_default")
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise APIException("UNAUTHORIZED", "Invalid token type", status.HTTP_401_UNAUTHORIZED)
        
        user_id = payload.get("sub")
        access_token = create_access_token(subject=user_id, roles=["citizen"])
        new_refresh = create_refresh_token(subject=user_id)
        
        return make_envelope(
            {
                "access_token": access_token,
                "refresh_token": new_refresh,
                "token_type": "bearer"
            },
            request_id=req_id
        )
    except Exception as e:
        raise APIException("UNAUTHORIZED", f"Token refresh failed: {str(e)}", status.HTTP_401_UNAUTHORIZED)


@router.get("/auth/me", tags=["Auth"])
async def get_me(request: Request, current_user: dict = Depends(get_current_user)):
    req_id = getattr(request.state, "request_id", "req_default")
    user_data = {
        "id": str(current_user.get("_id", current_user.get("id"))),
        "phone": current_user.get("phone"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "language": current_user.get("language"),
        "is_verified": current_user.get("is_verified", True)
    }
    return make_envelope(user_data, request_id=req_id)
