import os
import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

pool: asyncpg.Pool | None = None


async def init_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


async def close_pool():
    global pool
    if pool:
        await pool.close()


async def get_db() -> asyncpg.Connection:
    """Get a connection from the pool."""
    async with pool.acquire() as conn:
        yield conn
