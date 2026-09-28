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
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# ── Supabase Auth ──
# Emails that get the admin (District Coordinator) role when they sign in with Supabase Auth.
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

# Legacy passwordless endpoints (/auth/login, /auth/register/public, /auth/register/fieldworker)
# accept any email with no verification, so they are disabled unless explicitly turned on.
ALLOW_LEGACY_AUTH = os.getenv("ALLOW_LEGACY_AUTH", "false").strip().lower() in ("1", "true", "yes")

# When SUPABASE_DB_URL is present, database mode is Supabase PostgreSQL.
# Otherwise the app uses a local SQLite file that is created and seeded with demo data.
USE_SUPABASE = bool(SUPABASE_DB_URL)
_default_local_db = "/tmp/shohay_local.db" if os.getenv("VERCEL") else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "shohay_local.db"
)
LOCAL_DB_URL = os.getenv("LOCAL_DB_URL", f"sqlite:///{_default_local_db}")

# ── Authentication & OTP Configuration ──
OTP_EXPIRATION_SECONDS = int(os.getenv("OTP_EXPIRATION_SECONDS", "300"))  # 5 minutes
JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
TOKEN_EXPIRATION_DAYS = int(os.getenv("TOKEN_EXPIRATION_DAYS", "30"))

# ── Twilio Configuration (SMS OTP for phone login) ──
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
TWILIO_CONFIGURED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)

# ── Resend Configuration (Email OTP for email login) ──
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Shohay Emergency <onboarding@resend.dev>").strip()
RESEND_CONFIGURED = bool(RESEND_API_KEY)

# ── SSLCommerz Payment Gateway (donations) ──
# Sandbox by default using SSLCommerz's published public demo store — real sandbox
# transactions, no signup needed. Swap in your own free sandbox store_id/store_passwd
# from https://developer.sslcommerz.com/registration/ any time; set SSLCOMMERZ_SANDBOX=false
# only once you have real production credentials.
SSLCOMMERZ_STORE_ID = os.getenv("SSLCOMMERZ_STORE_ID", "testbox").strip()
SSLCOMMERZ_STORE_PASSWORD = os.getenv("SSLCOMMERZ_STORE_PASSWORD", "qwerty").strip()
SSLCOMMERZ_SANDBOX = os.getenv("SSLCOMMERZ_SANDBOX", "true").strip().lower() in ("1", "true", "yes")
SSLCOMMERZ_BASE_URL = "https://sandbox.sslcommerz.com" if SSLCOMMERZ_SANDBOX else "https://securepay.sslcommerz.com"

# Publicly reachable backend URL — SSLCommerz calls success/fail/cancel/ipn here
# server-to-server, so this can never be localhost, even in local development.
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "https://shohaybackend.vercel.app").strip().rstrip("/")

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
- UAV (drone) detections of stranded people, turned into rescue requests
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
