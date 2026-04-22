import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .database import init_pool, close_pool
from .rate_limit import limiter
from .routers import auth_router, profile_router, chat_router, settings_router, error_analysis_router, admin_router, onboarding_router, internal_router

# ── Structured logging ────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("academie-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    limiter.start_cleanup()
    logger.info("API started — DB pool + rate limiter ready")
    yield
    await close_pool()
    logger.info("API shutdown — DB pool closed")


app = FastAPI(
    title="Academie-IA API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow SvelteKit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:5173", "https://academie.petit-pont.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(profile_router.router)
app.include_router(chat_router.router)
app.include_router(settings_router.router)
app.include_router(error_analysis_router.router)
app.include_router(admin_router.router)
app.include_router(onboarding_router.router)
from .routers import consolidation_router  # noqa: E402
app.include_router(consolidation_router.router)
app.include_router(internal_router.router)


# ── Request logging middleware ────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000)
    # Skip health checks from noise
    if request.url.path != "/api/health":
        logger.info(
            "%s %s → %d (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
    return response


@app.get("/api/health")
async def health():
    """Healthcheck endpoint — used by Docker HEALTHCHECK."""
    from . import database as db

    try:
        await db.pool.fetchval("SELECT 1")
        return {"status": "ok", "service": "academie-api", "db": "connected"}
    except Exception:
        return {"status": "degraded", "service": "academie-api", "db": "disconnected"}
