from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, wg, me


def create_app() -> FastAPI:
    app = FastAPI(title="SpartaRocket WG API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(wg.router)
    app.include_router(me.router)

    return app


app = create_app()
