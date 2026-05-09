from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="CS423 Grading Platform", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Routes mounted under /api so the frontend Vite proxy can forward cleanly.
    # Health endpoint and feature routers are added in subsequent steps.

    return app


app = create_app()
