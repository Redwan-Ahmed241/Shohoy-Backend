import os
from typing import List

# Automatically load .env file if present in local development
try:
    from dotenv import load_dotenv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(base_dir, ".env"))
    load_dotenv()
except ImportError:
    pass

# ── Environment & Supabase Config ──
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
raw_db_url = os.getenv("SUPABASE_DB_URL", "").strip()

# Normalize postgres:// to postgresql:// (Supabase dashboard sometimes supplies postgres://)
if raw_db_url.startswith("postgres://"):
    SUPABASE_DB_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    SUPABASE_DB_URL = raw_db_url

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# When SUPABASE_DB_URL is present, database mode is Supabase PostgreSQL.
# Otherwise, falls back gracefully to in-memory mock storage.
USE_SUPABASE = bool(SUPABASE_DB_URL)

# ── App Metadata ──
PROJECT_NAME = "Shohay Flood Relief & Disaster Response API"
API_V1_PREFIX = "/api"
VERSION = "1.0.0"
DESCRIPTION = """
### Shohay Backend API
An emergency response coordination platform providing:
- Real-time flood and severe weather alert feeds
- Shelter capacity, status, and navigation routing
- Multi-step assistance request submissions and tracking
- Relief campaign aggregations & donation metrics
- 24/7 verified emergency contact directories
- Volunteer coordination & assignment tracking
- Relief supply warehouse inventory and low-stock monitoring
"""

# ── CORS ──
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:4173",
    "https://shohay-bd.vercel.app",
]

# Allow additional custom origins via environment variable
ADDITIONAL_CORS_ORIGINS = os.getenv("ADDITIONAL_CORS_ORIGINS", "")
if ADDITIONAL_CORS_ORIGINS:
    CORS_ORIGINS.extend([o.strip() for o in ADDITIONAL_CORS_ORIGINS.split(",") if o.strip()])

# Permissive regex for Vercel preview & production deployments
CORS_ORIGIN_REGEX = r"^https://.*\.vercel\.app$"
