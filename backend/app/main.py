"""Grove FastAPI application — composition root.

Route handlers live in `app/routers/` (content, tests, misc); request models
in `app/routers/requests.py`; response models in `app/schemas.py`. This file
only wires middleware, security and routers together.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import content, misc, tests
from .security import install_security

app = FastAPI(title=settings.app_name, version="0.1.0",
              docs_url="/api/docs", openapi_url="/api/openapi.json")
install_security(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "version": app.version}


app.include_router(content.router)
app.include_router(tests.router)
app.include_router(misc.router)
