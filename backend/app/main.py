"""Priority — FastAPI Application Entry Point."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Priority",
    description=(
        "AI-assisted daily health coach for college students. "
        "Answers one question: 'What is the most important health action I should take today?'"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Flutter dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Narrow this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    """Create tables on startup (dev mode). Use Alembic migrations in production."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created.")


@app.get("/")
def root():
    return {
        "app": "Priority",
        "version": "0.1.0",
        "description": "What is the most important health action you should take today?",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
