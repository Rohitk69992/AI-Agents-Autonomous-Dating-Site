#!/usr/bin/env python3
"""
Seed Demo Participants Script for AuraMatch AI
================================================
Idempotently seeds exactly 25 realistic, fully synthetic development fixtures into the database.
Safe for local SQLite development and production PostgreSQL on Render.

Usage:
    # 1. Local execution using default settings / SQLite:
    python scripts/seed_demo_participants.py

    # 2. Fast seeding without dating simulations:
    python scripts/seed_demo_participants.py --no-simulate

    # 3. Production execution against PostgreSQL on Render:
    DATABASE_URL="postgresql://user:pass@host/db" python scripts/seed_demo_participants.py
"""

import argparse
import os
import sys
import logging

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("seed_demo_participants")

def mask_db_url(url: str) -> str:
    """Mask password credentials in database connection string for safe logging."""
    if "@" in url:
        prefix = url.split("://")[0] + "://" if "://" in url else ""
        host_part = url.split("@")[-1]
        return f"{prefix}****:****@{host_part}"
    return url

def main():
    parser = argparse.ArgumentParser(description="Seed 25 synthetic participants for AuraMatch AI")
    parser.add_argument(
        "--no-simulate",
        action="store_true",
        help="Skip dating simulations and ranking calculations (seed participants & analyzed profiles only)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Explicit database URL override (overrides DATABASE_URL environment variable)"
    )
    args = parser.parse_args()

    # Override DATABASE_URL if explicitly provided
    if args.db_url:
        os.environ["DATABASE_URL"] = args.db_url

    from app.core.config import settings
    from app.db.base import Base
    from app.db.session import engine, SessionLocal
    from app.db.seed_demo import seed_database, DEMO_PARTICIPANTS

    masked_url = mask_db_url(settings.DATABASE_URL)
    logger.info("==================================================")
    logger.info("   AuraMatch AI — Synthetic Cohort Seeder        ")
    logger.info("==================================================")
    logger.info(f"Target Database: {masked_url}")
    logger.info(f"Target Fixtures: {len(DEMO_PARTICIPANTS)} synthetic profiles")
    logger.info(f"Run Simulation : {not args.no_simulate}")
    logger.info("--------------------------------------------------")

    # Ensure tables exist
    logger.info("Verifying database schema...")
    Base.metadata.create_all(bind=engine)

    # Execute idempotent seed
    db = SessionLocal()
    try:
        results = seed_database(db=db, run_simulation=not args.no_simulate)
        logger.info("--------------------------------------------------")
        logger.info("Seeding completed successfully!")
        logger.info(f"  • Created participants : {results['created_participants']}")
        logger.info(f"  • Existing participants: {results['existing_participants']}")
        logger.info(f"  • Total in database    : {results['total_participants']}")
        logger.info(f"  • Simulated sessions   : {results.get('simulated_sessions', 0)}")
        logger.info("==================================================")
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
