import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import init_pool, close_pool
from .rate_limit import limiter
from . import sessions as session_store
from .auth import COOKIE_CSRF
from .routers import auth_router, profile_router, chat_router, settings_router, error_analysis_router, admin_router, onboarding_router, internal_router, security_router

# ── Structured logging ────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("academie-api")

# ── Phase B4 — Sentry / GlitchTip error tracking (no-op si DSN absent) ───
_SENTRY_DSN = os.environ.get("SENTRY_DSN_BACKEND", "").strip()
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    def _scrub_pii(event, hint):
        """Drop session cookies, CSRF headers, password from request body."""
        req = event.get("request") or {}
        if "cookies" in req:
            req["cookies"] = {}
        headers = req.get("headers") or {}
        for h in ("cookie", "Cookie", "x-csrf-token", "X-CSRF-Token", "authorization", "Authorization"):
            headers.pop(h, None)
        data = req.get("data")
        if data and isinstance(data, (dict, str)):
            data_str = str(data).lower()
            if "password" in data_str or "secret" in data_str:
                req["data"] = "<scrubbed>"
        if "user" in event:
            event["user"] = {"id": "<redacted>"}
        return event

    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        traces_sample_rate=0.10,
        environment=os.environ.get("ENV", "production"),
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
        ],
        send_default_pii=False,
        before_send=_scrub_pii,
    )
    logger.info("Sentry/GlitchTip backend tracking enabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    limiter.start_cleanup()
    # A1 — open Redis connection pool
    session_store._client()
    logger.info("API started — DB pool + Redis pool + rate limiter ready")
    yield
    await close_pool()
    await session_store.close_pool()
    logger.info("API shutdown — DB pool + Redis pool closed")


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
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


# A1 — CSRF double-submit cookie protection.
# Bootstrap endpoints (login flows + un-authed telemetry) are exempted ;
# the rest enforces strict header == cookie equality on mutations.
_CSRF_EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/login-mfa",
    "/api/csp-report",
    "/api/telemetry/onboarding-event",
    "/api/sentry-tunnel",  # Phase B4 — Sentry SDK envelope ingestion proxy
}
_CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    if request.method in _CSRF_SAFE_METHODS or request.url.path in _CSRF_EXEMPT_PATHS:
        return await call_next(request)
    cookie_token = request.cookies.get(COOKIE_CSRF)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or cookie_token != header_token:
        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF token manquant ou invalide"},
        )
    return await call_next(request)

# Security headers — refactor 2026-H2 Phase A3.
# CSP itself is set on HTML responses by SvelteKit hooks.server.ts (HTML pages
# need per-document CSP with nonces; FastAPI only emits JSON/streams).
# Here we cover the cross-cutting headers that apply to all responses.
_PERMISSIONS_POLICY = ", ".join([
    "accelerometer=()", "ambient-light-sensor=()", "autoplay=()",
    "battery=()", "camera=()", "cross-origin-isolated=()",
    "display-capture=()", "document-domain=()", "encrypted-media=()",
    "execution-while-not-rendered=()", "execution-while-out-of-viewport=()",
    "fullscreen=()", "geolocation=()", "gyroscope=()",
    "keyboard-map=()", "magnetometer=()", "microphone=()",
    "midi=()", "navigation-override=()", "payment=()",
    "picture-in-picture=()", "publickey-credentials-get=()",
    "screen-wake-lock=()", "sync-xhr=()", "usb=()",
    "web-share=()", "xr-spatial-tracking=()",
])

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = _PERMISSIONS_POLICY
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
from .routers import agents_router  # noqa: E402
app.include_router(agents_router.router)
app.include_router(security_router.router)
from .routers import webauthn_router  # noqa: E402
app.include_router(webauthn_router.router)


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


# ── Phase B4 — Sentry tunnel proxy (browser → FastAPI → glitchtip-web) ─
# Reuses the existing /api/* path so sinse's CF Access cookie covers it.
# Avoids the path-precedence bug we hit with a CF Access bypass app
# at academie.petit-pont.com/sentry-tunnel.
import httpx as _httpx
from fastapi import Response as _Response

_GLITCHTIP_INTERNAL_BASE = (
    os.environ.get("SENTRY_DSN_BACKEND", "")
    .replace("//", "//::").split("//::")[1].split("@")[1].split("/")[0]
    if os.environ.get("SENTRY_DSN_BACKEND") else "glitchtip-web:8000"
)


@app.post("/api/sentry-tunnel")
async def sentry_tunnel(request: Request):
    """Forward Sentry envelope to glitchtip-web internally. Bypasses CF Access
    + CSP `connect-src 'self'` injected by Cosmos."""
    body = await request.body()
    text = body.decode("utf-8", errors="replace")
    first_line = text.split("\n", 1)[0]
    project_id = None
    try:
        import json as _json
        header = _json.loads(first_line)
        if header.get("dsn"):
            from urllib.parse import urlparse
            project_id = urlparse(header["dsn"]).path.lstrip("/")
    except Exception:
        pass
    if not project_id:
        return _Response(content="missing project id", status_code=400)
    target = f"http://{_GLITCHTIP_INTERNAL_BASE}/api/{project_id}/envelope/"
    async with _httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            target,
            content=body,
            headers={"Content-Type": "application/x-sentry-envelope"},
        )
    return _Response(status_code=r.status_code)
