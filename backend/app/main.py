import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.v1.participants import router as participants_router
from app.api.v1.dates import router as dates_router
from app.api.v1.rankings import router as rankings_router
from app.api.v1.runs import router as runs_router
from app.api.v1.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agentic_dating")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

    # Auto-seed database if empty so judges and live deployments have instant demo data
    try:
        from app.db.session import SessionLocal
        from app.models.participant import Participant
        from app.db.seed_demo import seed_database

        with SessionLocal() as db:
            p_count = db.query(Participant).count()
            if p_count == 0:
                logger.info("Database is empty (0 participants). Triggering automatic demo seeding...")
                seed_database(db=db, run_simulation=True)
                logger.info("Automatic demo seeding completed successfully.")
            else:
                logger.info(f"Database already populated ({p_count} participants found). Skipping auto-seed.")
    except Exception as e:
        logger.warning(f"Auto-seed check encountered an issue (non-fatal): {e}")

    yield
    logger.info("Application shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="End-to-End Autonomous Agentic Dating Platform with Genuine Multi-Agent Interactions, Traceable Profile Evidence, and Explainable Compatibility Rankings.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS configuration: strict allowed origins with regex fallback for preview domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(participants_router, prefix=settings.API_V1_STR)
app.include_router(dates_router, prefix=settings.API_V1_STR)
app.include_router(rankings_router, prefix=settings.API_V1_STR)
app.include_router(runs_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = str(uuid.uuid4())
    logger.exception(f"Unhandled error [{correlation_id}] processing {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "correlation_id": correlation_id
        }
    )

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": f"{settings.API_V1_STR}/docs"
    }
