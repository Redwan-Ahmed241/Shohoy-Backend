"""
Demo data for the LOCAL SQLite database only (never runs against Supabase).
Lets teammates run every screen — public, volunteer, admin and UAV — without
production credentials.
"""
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Type

from sqlalchemy import DateTime
from sqlalchemy.orm import Session

from . import mock_data as m
from .models import (
    AlertModel, ShelterModel, CampaignModel, ContactModel, AssistanceRequestModel,
    VolunteerProfileModel, VolunteerAssignmentModel, WarehouseItemModel, UserModel,
    UavDroneModel,
)

# Local-only demo drone, used by scripts/simulate_drone.py
DEMO_DRONE_REGISTRATION_ID = "DEMO-UAV-01"
DEMO_DRONE_API_KEY = "local-demo-drone-key"

DEMO_ADMIN = {
    "id": "usr-admin-001",
    "role": "admin",
    "first_name": "District",
    "last_name": "Coordinator",
    "phone_number": "01912345678",
    "email": "coordinator@shohay.local",
    "gender": "Other",
    "skills": [],
    "equipment": [],
    "verification_status": "Verified",
}


def _camel_to_snake(key: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()


def _to_row(model: Type, data: Dict[str, Any]):
    """Maps a camelCase mock dict onto a model, skipping unknown keys and string timestamps."""
    columns = model.__table__.columns
    values = {}
    for key, value in data.items():
        col = _camel_to_snake(key)
        if col not in columns:
            continue
        if isinstance(value, str) and isinstance(columns[col].type, DateTime):
            continue
        values[col] = value
    return model(**values)


def seed_if_empty(db: Session) -> None:
    if db.query(UserModel).first() is not None:
        return

    for model, rows in [
        (AlertModel, m.MOCK_ALERTS),
        (ShelterModel, m.MOCK_SHELTERS),
        (CampaignModel, m.MOCK_CAMPAIGNS),
        (ContactModel, m.MOCK_CONTACTS),
        (VolunteerAssignmentModel, m.MOCK_VOLUNTEER_ASSIGNMENTS),
        (WarehouseItemModel, m.MOCK_WAREHOUSE_ITEMS),
        (AssistanceRequestModel, list(m.MOCK_REQUESTS_DB.values())),
        (UserModel, m.MOCK_USERS + [DEMO_ADMIN]),
    ]:
        db.add_all(_to_row(model, row) for row in rows)

    for user in m.MOCK_USERS:
        if user["role"] == "fieldworker":
            db.add(VolunteerProfileModel(
                id=user["id"],
                name=f"{user['first_name']} {user['last_name']}",
                code=f"VOL-{hashlib.sha1(user['id'].encode()).hexdigest()[:8].upper()}",
                district="Sunamganj",
                join_date=datetime.utcnow().strftime("%d %B %Y"),
                skills=user.get("skills", []),
                rating=4.8,
            ))

    db.add(UavDroneModel(
        id="drone-demo-01",
        name="Sunamganj Scout 1",
        registration_id=DEMO_DRONE_REGISTRATION_ID,
        api_key_hash=hashlib.sha256(DEMO_DRONE_API_KEY.encode()).hexdigest(),
        district="Sunamganj",
    ))
    db.commit()
