import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import Participant
from app.db.seed_demo import seed_database
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
    
    # Auto-seed demonstration run if database is empty
    db = SessionLocal()
    try:
        count = db.query(Participant).count()
        if count == 0:
            logger.info("Database is empty. Automatically initializing the 25-participant demonstration dataset...")
            seed_database(db=db, run_simulation=True)
            logger.info("Automatic seeding complete.")
    except Exception as e:
        logger.error(f"Error during initial seed: {e}")
    finally:
        db.close()

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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local dev and preview hosts
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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error processing {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": f"{settings.API_V1_STR}/docs"
    }
