"""
Shared FastAPI dependencies: who is calling, and are they allowed to?

    Depends(get_current_user)                    -> any signed-in user
    Depends(require_roles("admin"))              -> coordinators only
    Depends(require_roles("fieldworker", "admin")) -> field volunteers (and coordinators)
    Depends(get_current_drone)                   -> a registered drone (X-Drone-Id / X-Drone-Token)
"""
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import config
from database.connection import get_db
from database.models import UavDroneModel
from database.repository import RepositoryError, repo
from database.uav_repository import uav_repo
from schemas.auth import AuthUser
from services.otp_service import otp_service


@contextmanager
def repository_errors() -> Iterator[None]:
    """Turns RepositoryError (e.g. 'task already taken') into the matching HTTP error."""
    try:
        yield
    except RepositoryError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


def require_legacy_auth():
    """Blocks the unverified passwordless endpoints unless ALLOW_LEGACY_AUTH is set."""
    if not config.ALLOW_LEGACY_AUTH:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This sign-in method is disabled. Sign in with a one-time code via Supabase Auth."
        )


def resolve_supabase_user(db: Session, claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns the users row for a verified Supabase Auth identity, creating it on first sign-in.
    Existing accounts are linked by verified email or phone. The role always comes from the
    database (or ADMIN_EMAILS), never from the client.
    """
    uid = claims["sub"]
    email = (claims.get("email") or "").strip().lower() or None
    phone = claims.get("phone")
    meta = claims.get("user_metadata") or {}
    is_admin_email = email is not None and email in config.ADMIN_EMAILS

    user = (
        repo.get_user_by_id(db, uid)
        or (email and repo.get_user_by_email(db, email))
        or (phone and repo.get_user_by_phone(db, phone))
    )
    if user:
        if is_admin_email and user.get("role") != "admin":
            user = repo.update_user(db, user["id"], {"role": "admin"}) or user
        return user

    if is_admin_email:
        role, def_first, def_last = "admin", "District", "Coordinator"
    elif meta.get("requested_role") in ("fieldworker", "volunteer"):
        role, def_first, def_last = "fieldworker", "Field", "Volunteer"
    else:
        role, def_first, def_last = "public", "Public", "Citizen"

    first_name = (meta.get("first_name") or "").strip() or def_first
    last_name = (meta.get("last_name") or "").strip() or def_last
    user_payload = {
        "id": uid,
        "role": role,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone or (meta.get("phone") or "").strip() or None,
        "email": email,
        "avatar": f"https://api.dicebear.com/7.x/initials/svg?seed={first_name}+{last_name}",
        "gender": None,
        "skills": [],
        "equipment": [],
        "nid_number": None,
        "address": None,
        "dob": None,
        "experience_certificate": None,
        "verification_status": "Pending" if role == "fieldworker" else "Verified"
    }
    try:
        return repo.create_user(db, user_payload)
    except IntegrityError:
        # A concurrent first request already created this user.
        db.rollback()
        return repo.get_user_by_id(db, uid)


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> AuthUser:
    """Decodes the Bearer token (Supabase or internal) and returns the signed-in user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in. Header 'Authorization: Bearer <token>' missing or invalid."
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = otp_service.decode_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or malformed authentication token."
        )

    if payload.get("supabase"):
        return AuthUser(**resolve_supabase_user(db, payload))

    user_data = repo.get_user_by_id(db, payload["sub"])
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account matching this token was not found."
        )
    return AuthUser(**user_data)


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[AuthUser]:
    """Like get_current_user, but returns None instead of 401 when signed out — for endpoints
    that work anonymously but attach the signed-in identity when one is present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return get_current_user(authorization=authorization, db=db)
    except HTTPException:
        return None


def require_roles(*roles: str):
    """Dependency factory: only users whose role is in `roles` get through (403 otherwise)."""
    def checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to do this."
            )
        return current_user
    return checker


def get_current_drone(
    db: Session = Depends(get_db),
    x_drone_id: Optional[str] = Header(None, alias="X-Drone-Id"),
    x_drone_token: Optional[str] = Header(None, alias="X-Drone-Token"),
) -> UavDroneModel:
    """Authenticates a drone by its registration ID and API key headers."""
    if not x_drone_id or not x_drone_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Drone authentication required.")
    drone = uav_repo.authenticate_drone(db, x_drone_id, x_drone_token)
    if drone is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid drone credentials.")
    return drone
