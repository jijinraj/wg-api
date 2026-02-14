import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.ops.router import router as ops_router
from app.modules.user.router import router as user_router
from app.modules.vpn.router import router as vpn_router

log = logging.getLogger("uvicorn")

def create_app() -> FastAPI:
    app = FastAPI(title="SpartaRocket WG API")
    
    @app.on_event("startup")
    async def _startup_log():
        if settings.DEV_MODE:
            log.warning("⚠️  SpartaRocket WG API is running in DEV MODE.")
        else:
            log.info("SpartaRocket WG API is running in production mode.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Domain modules
    app.include_router(user_router)
    app.include_router(vpn_router)
    app.include_router(admin_router)
    app.include_router(ops_router)
    app.include_router(auth_router)

    return app

app = create_app()
