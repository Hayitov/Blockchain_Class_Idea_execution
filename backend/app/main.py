from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import routes as auth_routes
from app.routes import assignments, health, submissions
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

    app.include_router(health.router)
    app.include_router(auth_routes.router)
    app.include_router(assignments.router)
    app.include_router(submissions.router)

    return app


app = create_app()
