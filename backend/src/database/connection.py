"""
Digital FTE Customer Success Agent - Database Connection Pool
PostgreSQL connection management with asyncpg for high-performance async operations
"""

import asyncpg
from typing import Optional
import logging
from contextlib import asynccontextmanager

from ..utils.config import get_settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def create_pool() -> asyncpg.Pool:
    """
    Create PostgreSQL connection pool with asyncpg.

    Returns:
        asyncpg.Pool: Connection pool instance
    """
    global _pool

    if _pool is not None:
        logger.warning("Connection pool already exists")
        return _pool

    settings = get_settings()

    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,
            max_size=settings.database_max_connections,
            command_timeout=60,
            server_settings={
                'application_name': 'digital_fte_agent'
            }
        )
        logger.info(
            f"PostgreSQL connection pool created: "
            f"min_size=2, max_size={settings.database_max_connections}"
        )
        return _pool
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise


async def close_pool() -> None:
    """Close the PostgreSQL connection pool gracefully."""
    global _pool

    if _pool is None:
        logger.warning("No connection pool to close")
        return

    await _pool.close()
    _pool = None
    logger.info("PostgreSQL connection pool closed")


async def get_pool() -> asyncpg.Pool:
    """
    Get the existing connection pool or create one if it doesn't exist.

    Returns:
        asyncpg.Pool: Connection pool instance
    """
    global _pool

    if _pool is None:
        _pool = await create_pool()

    return _pool


@asynccontextmanager
async def get_connection():
    """
    Context manager for acquiring a database connection from the pool.

    Usage:
        async with get_connection() as conn:
            result = await conn.fetch("SELECT * FROM customers")

    Yields:
        asyncpg.Connection: Database connection
    """
    pool = await get_pool()

    async with pool.acquire() as connection:
        yield connection


@asynccontextmanager
async def get_transaction():
    """
    Context manager for database transactions.
    Automatically commits on success, rolls back on exception.

    Usage:
        async with get_transaction() as tx:
            await tx.execute("INSERT INTO customers ...")
            await tx.execute("INSERT INTO customer_identifiers ...")

    Yields:
        asyncpg.Connection: Database connection in transaction
    """
    pool = await get_pool()

    async with pool.acquire() as connection:
        async with connection.transaction():
            yield connection


async def execute_query(query: str, *args) -> str:
    """
    Execute a SQL query without returning results (INSERT, UPDATE, DELETE).

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        str: Result status (e.g., "INSERT 0 1")
    """
    async with get_connection() as conn:
        result = await conn.execute(query, *args)
        return result


async def fetch_one(query: str, *args) -> Optional[asyncpg.Record]:
    """
    Fetch a single row from the database.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        Optional[asyncpg.Record]: Single row or None
    """
    async with get_connection() as conn:
        return await conn.fetchrow(query, *args)


async def fetch_all(query: str, *args) -> list[asyncpg.Record]:
    """
    Fetch all rows from the database.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        list[asyncpg.Record]: List of rows
    """
    async with get_connection() as conn:
        return await conn.fetch(query, *args)


async def fetch_val(query: str, *args) -> any:
    """
    Fetch a single value from the database.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        any: Single value
    """
    async with get_connection() as conn:
        return await conn.fetchval(query, *args)


async def health_check() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_pgvector_extension() -> bool:
    """
    Check if pgvector extension is installed and enabled.

    Returns:
        bool: True if pgvector is available, False otherwise
    """
    try:
        query = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        result = await fetch_val(query)
        return result == 1
    except Exception as e:
        logger.error(f"pgvector extension check failed: {e}")
        return False
