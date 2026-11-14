"""LARA OS — FastAPI Orchestrator Main Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.api.websocket import ws_router

from app.proactivity.scheduler import proactivity_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lara.orchestrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("🚀 LARA OS Orchestrator initializing — Autonomous Intelligence Engine")
    logger.info("📡 Environment: %s", settings.ENVIRONMENT)
    logger.info("🤖 Model Target: %s", settings.MODEL_NAME)
    logger.info("🔑 Gemini API Key configured: %s", bool(settings.GEMINI_API_KEY))
    logger.info("🌐 CORS Origins: %s", settings.CORS_ORIGINS)
    logger.info("=" * 60)

    # Start background proactivity engine
    proactivity_scheduler.start()

    yield

    # Stop background proactivity engine
    proactivity_scheduler.stop()
    logger.info("🛑 LARA OS Orchestrator shutting down.")


app = FastAPI(
    title="LARA OS Orchestrator",
    description="JARVIS-style Personal AI OS Orchestration Engine (Phase 0 Skeleton)",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend and mobile devices on local LAN
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API and WebSocket routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root landing check."""
    return {
        "system": "LARA OS Orchestrator",
        "phase": "Phase 0 (Skeleton)",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
