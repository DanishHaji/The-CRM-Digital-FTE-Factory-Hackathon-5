#!/usr/bin/env python3
"""
Digital FTE API Server Runner

Convenience script to start the FastAPI application with uvicorn.

Usage:
    python run_api.py                    # Start with default settings
    python run_api.py --host 0.0.0.0     # Specify host
    python run_api.py --port 8080        # Specify port
    python run_api.py --reload           # Enable auto-reload (development)
    python run_api.py --workers 4        # Specify number of workers (production)

Environment:
    Set environment variables in .env file or export them:
    - DATABASE_URL
    - KAFKA_BROKER
    - OPENAI_API_KEY
    - etc.
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def main():
    """Parse arguments and start the API server."""

    parser = argparse.ArgumentParser(
        description="Digital FTE Customer Success Agent API Server"
    )

    parser.add_argument(
        "--host",
        default=settings.api_host,
        help=f"Bind host (default: {settings.api_host})"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=settings.api_port,
        help=f"Bind port (default: {settings.api_port})"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Number of worker processes (default: {settings.api_workers})"
    )

    parser.add_argument(
        "--log-level",
        default=settings.log_level.lower(),
        choices=["debug", "info", "warning", "error", "critical"],
        help=f"Log level (default: {settings.log_level.lower()})"
    )

    args = parser.parse_args()

    # Log startup info
    logger.info(
        "starting_api_server",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        environment=settings.environment,
    )

    # Start server
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers or settings.api_workers if not args.reload else None,
        log_level=args.log_level,
        access_log=True,
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
