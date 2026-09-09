"""
Database connection management for Supabase PostgreSQL via SQLAlchemy 2.0.
Configured specifically for serverless deployments (Vercel) and transaction poolers.
"""
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.pool import NullPool
import config

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass

engine = None
SessionLocal = None

def init_engine(db_url: Optional[str] = None):
    """Initialize or re-initialize database engine."""
    global engine, SessionLocal
    url = db_url or config.SUPABASE_DB_URL
    if not url:
        engine = None
        SessionLocal = None
        return None

    # Normalize driver prefix
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_engine(url, connect_args=connect_args)
    else:
        # PostgreSQL / Supabase
        # Use NullPool for serverless function environments (Vercel) to prevent connection leaks
        connect_args["options"] = "-c timezone=utc"
        engine = create_engine(
            url,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args=connect_args
        )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

if config.USE_SUPABASE:
    init_engine()

def get_session() -> Optional[Session]:
    """Return a new database session or None if not configured."""
    if SessionLocal is None:
        return None
    return SessionLocal()

def get_db() -> Generator[Optional[Session], None, None]:
    """
    FastAPI dependency that yields a database session.
    Yields None if Supabase is not configured, triggering fallback to in-memory store.
    """
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
