import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware

# Configure application logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("thirdeye")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown event handling."""
    logger.info("Initializing ThirdEye Dark Web Intelligence Platform Backend...")
    logger.info(f"Loaded Project: '{settings.PROJECT_NAME}' | Version: 2.0-SIH")
    logger.info(f"API Prefix: {settings.API_V1_STR} | Debug Mode: {settings.DEBUG}")
    logger.info(f"Configured CORS Origins: {settings.ALLOWED_ORIGINS}")
    
    # Place startup logic here (e.g., database connection pool initialization)
    yield
    
    # Place shutdown logic here (e.g., closing database connections, flushing logs)
    logger.info("Shutting down ThirdEye Backend service cleanly...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url="/redoc",
    lifespan=lifespan,
    version="2.0-SIH",
)

# Add custom Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS for Next.js frontend integration
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root Overview"])
async def root_overview():
    """Root metadata endpoint providing service overview and documentation links."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": "2.0-SIH",
        "documentation": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "status": "online",
    }


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )

