import os
from typing import List

PROJECT_NAME = "Shohay Flood Relief & Disaster Response API"
API_V1_PREFIX = "/api"
VERSION = "1.0.0"
DESCRIPTION = """
### Shohay (সহায়) Backend API
An emergency response coordination platform providing:
- Real-time flood and severe weather alert feeds
- Shelter capacity, status, and navigation routing
- Multi-step assistance request submissions and tracking
- Relief campaign aggregations & donation metrics
- 24/7 verified emergency contact directories
- Volunteer coordination & assignment tracking
- Relief supply warehouse inventory and low-stock monitoring
"""

# Allowed CORS origins for frontend web client (Vite dev server & production URLs)
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:4173",
    "*"  # Development permissive
]
