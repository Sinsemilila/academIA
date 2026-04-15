import os
import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# LiteLLM SpendLogs lives in litellm_db (same PG instance as academie_db)
LITELLM_DATABASE_URL = DATABASE_URL.rsplit("/", 1)[0] + "/litellm_db"

pool: asyncpg.Pool | None = None
litellm_pool: asyncpg.Pool | None = None


async def init_pool():
    global pool, litellm_pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    try:
        litellm_pool = await asyncpg.create_pool(LITELLM_DATABASE_URL, min_size=1, max_size=4)
    except Exception:
        litellm_pool = None  # SpendLogs unavailable → endpoints fall back to local estimate


async def close_pool():
    global pool, litellm_pool
    if pool:
        await pool.close()
    if litellm_pool:
        await litellm_pool.close()


async def get_db() -> asyncpg.Connection:
    """Get a connection from the pool."""
    async with pool.acquire() as conn:
        yield conn
