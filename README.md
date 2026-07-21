# Surakshak360 Backend API

Surakshak360 backend service built with Python and FastAPI. Implements authentication, case management, file storage presigned workflows, async job orchestration with ML microservices, real-time WebSocket communication, and structured logging.

## Project Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI application factory
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   ├── security.py         # JWT tokens & password hashing
│   │   ├── database.py         # MongoDB, Neo4j, Redis connections
│   │   ├── logging.py          # Structured JSON logging
│   │   └── exceptions.py       # Custom exception handlers & error envelope
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py       # Master API router
│   │   │   ├── deps.py         # FastAPI dependency injection
│   │   │   ├── routes/         # Endpoints (auth, users, cases, evidence, files, jobs, ws, health)
│   │   │   └── schemas/        # Request & Response Pydantic models
│   │   └── openapi.py          # Custom OpenAPI generator
│   ├── services/
│   │   ├── ml_client.py        # Async HTTP client for ML services
│   │   ├── file_storage.py     # Presigned upload URL generator
│   │   ├── notifications.py    # Notification dispatcher
│   │   ├── websocket.py        # Real-time WebSocket connection manager
│   │   └── case_workflow.py    # Case management business logic
│   └── tasks/
│       └── celery_app.py       # Async background worker tasks
├── tests/                      # Pytest unit & integration test suite
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── railway.toml                # Railway deployment settings
└── .env                        # Local environment variables
```

## Setup and Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run local development server:
```bash
uvicorn app.main:app --reload --port 8000
```

3. Run automated tests:
```bash
pytest tests/ -v
```

## API Documentation

- Swagger UI: `http://localhost:8000/v1/docs`
- ReDoc: `http://localhost:8000/v1/redoc`
- OpenAPI JSON Schema: `http://localhost:8000/v1/schema`
- Health check: `http://localhost:8000/health`
