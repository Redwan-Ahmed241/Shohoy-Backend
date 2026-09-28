"""
Database connection management via SQLAlchemy 2.0.

- SUPABASE_DB_URL set   -> Supabase PostgreSQL (production). NullPool keeps serverless
                           functions (Vercel) from leaking pooled connections.
- SUPABASE_DB_URL empty -> a local SQLite file (LOCAL_DB_URL). Tables are created and
                           filled with demo data automatically, so anyone can run the
                           full app without access to the production database.
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
    url = db_url or config.SUPABASE_DB_URL or config.LOCAL_DB_URL

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


def prepare_local_database():
    """Creates all tables in the local SQLite database and seeds demo data once."""
    from . import models  # noqa: F401  (registers every table on Base.metadata)
    from .seed import seed_if_empty

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)


init_engine()
if not config.USE_SUPABASE:
    prepare_local_database()


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
