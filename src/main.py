from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from src.core.config import settings
from src.core.database import engine, Base
from src.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Capvero Backend API...")
    
    # Create database tables (in production, use Alembic migrations)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Capvero Backend API...")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Capvero - Company Valuation & Succession Planning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint - health check.
    """
    return {
        "message": "Capvero Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": "capvero-backend"
    }
