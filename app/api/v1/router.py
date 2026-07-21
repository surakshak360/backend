from fastapi import APIRouter
from app.api.v1.routes import health, auth, users, cases, evidence, files, jobs, ws

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cases.router)
api_router.include_router(evidence.router)
api_router.include_router(files.router)
api_router.include_router(jobs.router)
api_router.include_router(ws.router)
