"""This module contains the FastAPI application for the backend."""

# Standard Library
import asyncio
import os

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

# Third Party Library
import logfire
import sentry_sdk

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from prometheus_client import CollectorRegistry, make_asgi_app, multiprocess
from redis import asyncio as aioredis

# Package Library
from chaturai import admin, chatur, recommendation
from chaturai.config import Settings
from chaturai.graphs.utils import create_graph_mappings
from chaturai.prometheus_middleware import PrometheusMiddleware
from chaturai.utils.browser import BrowserSessionStore
from chaturai.utils.general import make_dir
from chaturai.utils.logging_ import initialize_logger

DOMAIN_NAME = os.getenv("DOMAIN_NAME", "")
LOGGING_LEVEL = Settings.LOGGING_LOG_LEVEL
MODELS_EMBEDDING_OPENAI = Settings.MODELS_EMBEDDING_OPENAI
MODELS_EMBEDDING_ST = Settings.MODELS_EMBEDDING_ST
PLAYWRIGHT_PAGE_TTL = Settings.PLAYWRIGHT_PAGE_TTL
REDIS_HOST = Settings.REDIS_HOST
REDIS_PORT = Settings.REDIS_PORT
SENTRY_DSN = Settings.SENTRY_DSN
SENTRY_TRACES_SAMPLE_RATE = Settings.SENTRY_TRACES_SAMPLE_RATE

# Only need to initialize loguru once for the entire backend!
logger = initialize_logger(logging_level=LOGGING_LEVEL)

tags_metadata = [admin.TAG_METADATA, chatur.TAG_METADATA, recommendation.TAG_METADATA]


async def _browser_sweeper(app: FastAPI) -> None:
    """Background sweeper task to periodically clean up expired browser sessions.

    Parameters
    ----------
    app
        The application instance.
    """

    while True:
        await app.state.browser_session_store.sweep()
        await asyncio.sleep(PLAYWRIGHT_PAGE_TTL)


def create_app() -> FastAPI:
    """Create the FastAPI application for the backend. The process is as follows:

    1. Set up logfire for the app.
    2. Include routers for all the endpoints.
    3. Add CORS middleware for cross-origin requests.
    4. Add Prometheus middleware for metrics.
    5. Mount the metrics app on /metrics as an independent application.

    Returns
    -------
    FastAPI
        The application instance.
    """

    app = FastAPI(
        debug=True,
        lifespan=lifespan,
        openapi_tags=tags_metadata,
        title="ChaturAI APIs",
        swagger_ui_parameters={
            "swagger_js_url": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            "swagger_css_url": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        },
    )

    # 1.
    logfire.instrument_fastapi(app)
    logfire.instrument_httpx()
    logfire.instrument_redis(capture_statement=True)  # Set to `False` if sensitive data

    # 2.
    app.include_router(admin.routers.router)
    app.include_router(chatur.routers.router)
    app.include_router(recommendation.routers.router)

    origins = [
        f"http://{DOMAIN_NAME}",
        f"http://{DOMAIN_NAME}:3000",
        f"https://{DOMAIN_NAME}",
    ]

    # 3.
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_headers=["*"],
        allow_methods=["*"],
        allow_origins=origins,
    )

    # 4.
    app.add_middleware(PrometheusMiddleware)
    metrics_app = create_metrics_app()

    # 5.
    app.mount("/metrics", metrics_app)

    if not SENTRY_DSN or SENTRY_DSN == "" or SENTRY_DSN == "https://...":
        logger.log("ATTN", "No SENTRY_DSN provided. Sentry is disabled.")
    else:
        sentry_sdk.init(
            _experiments={"continuous_profiling_auto_start": True},
            dsn=SENTRY_DSN,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        )

    return app


def create_metrics_app() -> Callable:
    """Create prometheus metrics app

    Returns
    -------
    Callable
        The metrics app.
    """

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return make_asgi_app(registry=registry)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan events for the FastAPI application.

    The process is as follows:

    1. Connect to Redis.
    2. Set up Playwright automation procedures.
    3. Create graph descriptions for ChaturAI.
    4. Yield control to the application.
    5. Close the Redis connection when the application finishes.
    6. Stop Playwright when the application finishes.

    Parameters
    ----------
    app
        The application instance.
    """

    logger.info("Application started!")

    make_dir(Path(os.getenv("PATHS_LOGS_DIR", "/tmp")) / "chat_sessions")

    # 1.
    logger.info("Initializing Redis client...")
    app.state.redis = await aioredis.from_url(
        f"{REDIS_HOST}:{REDIS_PORT}", decode_responses=True
    )
    logger.success("Redis connection established!")

    # 2.
    logger.info("Setting up Playwright automation procedures...")
    pw = await async_playwright().start()
    app.state.browser = pw.chromium
    app.state.browser_session_store = BrowserSessionStore(ttl=PLAYWRIGHT_PAGE_TTL)
    asyncio.create_task(_browser_sweeper(app=app))
    logger.success("Finished setting up Playwright automation procedures!")

    # 3.
    logger.info("Loading graph descriptions for ChaturAI...")
    create_graph_mappings()
    logger.success("Finished loading graph descriptions for the ChaturAI!")

    logger.log("CELEBRATE", "Ready to roll! 🚀")

    # 4.
    yield

    # 5.
    logger.info("Closing Redis connection...")
    await app.state.redis.close()
    logger.success("Redis connection closed!")

    # 6.
    logger.info("Stopping Playwright...")
    await pw.stop()
    logger.success("Playwright stopped!")

    logger.success("Application finished!")
