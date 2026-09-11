from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.orm import Session

import config
from schemas.auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    PublicRegisterRequest,
    FieldworkerRegisterRequest,
    AuthUser,
    AuthResponse,
    ProfileUpdateRequest,
    AuthOptionsResponse,
    LoginRequest,
    OTPVerifyRequest
)
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db
from services.otp_service import otp_service
from services.sms_service import sms_service
from services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["Authentication & Profile"])


def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db: Optional[Session] = Depends(get_db)
) -> AuthUser:
    """
    Dependency that decodes Bearer token and returns the authenticated AuthUser.
    In local development, if no header is provided, returns demo user for testing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        if config.ENVIRONMENT in ("development", "test"):
            # Provide default demo user for convenience in dev
            user_data = supabase_repo.get_user_by_id(db, "usr-public-001") if db is not None else mem_db.get_user_by_id("usr-public-001")
            if user_data:
                return AuthUser(**user_data)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Header 'Authorization: Bearer <token>' missing or invalid."
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = otp_service.decode_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or malformed authentication token."
        )

    user_id = payload["sub"]
    user_data = supabase_repo.get_user_by_id(db, user_id) if db is not None else mem_db.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account matching this token was not found."
        )

    return AuthUser(**user_data)


# ── 1. SEND OTP (Phone via Twilio / Email via Resend) ──
@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send OTP to phone (Twilio) or email (Resend)"
)
def send_otp(request: SendOTPRequest, db: Optional[Session] = Depends(get_db)):
    """
    Dispatches a 6-digit security OTP to the user's mobile number or email address.
    - If phone number: Dispatched via Twilio SMS.
    - If email address: Dispatched via Resend with a responsive HTML template.
    - If API keys are not yet configured, automatically logs the OTP and returns debug_otp in development.
    """
    clean_id = request.identifier.strip()
    channel = request.channel

    if channel == "auto" or not channel:
        channel = "email" if "@" in clean_id else "phone"

    # Check if user already exists
    if db is not None:
        existing_user = supabase_repo.get_user_by_identifier(db, clean_id)
    else:
        existing_user = mem_db.get_user_by_identifier(clean_id)

    is_new = (existing_user is None)

    # Generate OTP code
    otp = otp_service.generate_otp(clean_id, channel=channel)

    # Dispatch via Twilio or Resend
    if channel == "phone":
        dispatch_result = sms_service.send_otp_sms(clean_id, otp)
    else:
        dispatch_result = email_service.send_otp_email(clean_id, otp)

    # In development or if keys not configured, surface OTP for developer convenience
    is_mock = dispatch_result.get("provider") == "mock" or config.ENVIRONMENT in ("development", "test")
    debug_otp = otp if is_mock else None

    return SendOTPResponse(
        success=True,
        identifier=clean_id,
        channel=channel,
        is_new_user=is_new,
        message=f"OTP dispatched to {clean_id} via {channel.capitalize()} ({dispatch_result.get('provider')}).",
        debug_otp=debug_otp
    )


# ── 2. VERIFY OTP ──
@router.post(
    "/verify-otp",
    response_model=AuthResponse,
    summary="Verify OTP code and authenticate or advance to profile creation"
)
def verify_otp(request: VerifyOTPRequest, db: Optional[Session] = Depends(get_db)):
    """
    Validates the 6-digit OTP:
    - If user exists: Issues persistent session bearer token and returns profile.
    - If user is new: Returns a temporary verification ticket to complete registration.
    """
    clean_id = request.identifier.strip()
    is_valid, msg = otp_service.verify_otp(clean_id, request.otp)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # Find existing account
    if db is not None:
        user_data = supabase_repo.get_user_by_identifier(db, clean_id)
    else:
        user_data = mem_db.get_user_by_identifier(clean_id)

    if user_data:
        token = otp_service.create_token({
            "sub": user_data["id"],
            "role": user_data.get("role", "public"),
            "phone": user_data.get("phoneNumber") or user_data.get("phone_number"),
            "email": user_data.get("email")
        })
        otp_service.clear_otp(clean_id)
        return AuthResponse(
            success=True,
            is_new_user=False,
            user=AuthUser(**user_data),
            token=token,
            message="Authentication successful. Welcome back to Shohay."
        )
    else:
        # New user: generate registration ticket
        ticket = otp_service.create_token({
            "sub": clean_id,
            "scope": "registration"
        }, expire_days=1)

        return AuthResponse(
            success=True,
            is_new_user=True,
            user=None,
            token=None,
            verification_ticket=ticket,
            message="OTP verified successfully. Please complete your registration profile."
        )


# ── 3. REGISTER: PUBLIC USER ──
@router.post(
    "/register/public",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Public user / volunteer profile"
)
def register_public(request: PublicRegisterRequest, db: Optional[Session] = Depends(get_db)):
    """
    Creates a minimal Public user profile:
    - First name, last name, phone, optional email
    - Skills (predefined + custom)
    - Equipment (predefined + custom)
    - Avatar, gender
    """
    # Check if user already exists
    identifier = request.phone_number or request.email or ""
    if identifier:
        existing = supabase_repo.get_user_by_identifier(db, identifier) if db is not None else mem_db.get_user_by_identifier(identifier)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with this phone or email already exists."
            )

    avatar_url = request.avatar or f"https://api.dicebear.com/7.x/initials/svg?seed={request.first_name}+{request.last_name}"

    user_payload = {
        "role": "public",
        "first_name": request.first_name.strip(),
        "last_name": request.last_name.strip(),
        "phone_number": request.phone_number.strip() if request.phone_number else None,
        "email": request.email.strip().lower() if request.email else None,
        "avatar": avatar_url,
        "gender": request.gender,
        "skills": request.skills,
        "equipment": request.equipment,
        "nid_number": None,
        "address": None,
        "dob": None,
        "experience_certificate": None,
        "verification_status": "Verified"
    }

    if db is not None:
        created_user = supabase_repo.create_user(db, user_payload)
    else:
        created_user = mem_db.create_user(user_payload)

    token = otp_service.create_token({
        "sub": created_user["id"],
        "role": "public",
        "phone": created_user.get("phoneNumber") or created_user.get("phone_number"),
        "email": created_user.get("email")
    })

    return AuthResponse(
        success=True,
        is_new_user=False,
        user=AuthUser(**created_user),
        token=token,
        message="Public profile successfully created. Welcome to Shohay!"
    )


# ── 4. REGISTER: FIELDWORKER ──
@router.post(
    "/register/fieldworker",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a Fieldworker profile with personal verification & certificates"
)
def register_fieldworker(request: FieldworkerRegisterRequest, db: Optional[Session] = Depends(get_db)):
    """
    Creates a Fieldworker profile with personal verification details:
    - Same as public profile (name, phone, mail, skills, equipment, avatar, gender)
    - Plus: NID number, residential address, Date of Birth (DOB), and optional experience certificate.
    """
    identifier = request.phone_number or request.email or ""
    if identifier:
        existing = supabase_repo.get_user_by_identifier(db, identifier) if db is not None else mem_db.get_user_by_identifier(identifier)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with this phone or email already exists."
            )

    avatar_url = request.avatar or f"https://api.dicebear.com/7.x/initials/svg?seed={request.first_name}+{request.last_name}"

    user_payload = {
        "role": "fieldworker",
        "first_name": request.first_name.strip(),
        "last_name": request.last_name.strip(),
        "phone_number": request.phone_number.strip() if request.phone_number else None,
        "email": request.email.strip().lower() if request.email else None,
        "avatar": avatar_url,
        "gender": request.gender,
        "skills": request.skills,
        "equipment": request.equipment,
        "nid_number": request.nid_number.strip(),
        "address": request.address.strip(),
        "dob": request.dob.strip(),
        "experience_certificate": request.experience_certificate.strip() if request.experience_certificate else None,
        "verification_status": "Pending"
    }

    if db is not None:
        created_user = supabase_repo.create_user(db, user_payload)
    else:
        created_user = mem_db.create_user(user_payload)

    token = otp_service.create_token({
        "sub": created_user["id"],
        "role": "fieldworker",
        "phone": created_user.get("phoneNumber") or created_user.get("phone_number"),
        "email": created_user.get("email")
    })

    return AuthResponse(
        success=True,
        is_new_user=False,
        user=AuthUser(**created_user),
        token=token,
        message="Fieldworker application submitted successfully. Verification is pending."
    )


# ── 5. AUTH OPTIONS (Predefined Skills, Equipment, Genders) ──
@router.get(
    "/options",
    response_model=AuthOptionsResponse,
    summary="Get predefined list of skills, equipment, genders, and roles"
)
def get_auth_options(db: Optional[Session] = Depends(get_db)):
    """
    Returns lists of predefined skills and equipment tags to easily render multi-select chips/checklists,
    while allowing users to type custom additions.
    """
    if db is not None:
        return supabase_repo.get_auth_options()
    return mem_db.get_auth_options()


# ── 6. CURRENT USER PROFILE ──
@router.get(
    "/me",
    response_model=AuthUser,
    summary="Get profile of currently logged-in user"
)
def get_current_user(current_user: AuthUser = Depends(get_current_user_from_token)):
    """
    Returns the authenticated user's profile based on the Authorization Bearer token.
    """
    return current_user


# ── 7. UPDATE PROFILE ──
@router.put(
    "/profile",
    response_model=AuthUser,
    summary="Update current user's profile (skills, equipment, avatar, etc.)"
)
def update_profile(
    updates: ProfileUpdateRequest,
    current_user: AuthUser = Depends(get_current_user_from_token),
    db: Optional[Session] = Depends(get_db)
):
    """
    Allows updating profile fields including custom skills, equipment, address, avatar, etc.
    """
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        return current_user

    if db is not None:
        updated = supabase_repo.update_user(db, current_user.id, update_data)
    else:
        updated = mem_db.update_user(current_user.id, update_data)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update profile; user not found."
        )

    return AuthUser(**updated)


# ── 8. LEGACY COMPATIBILITY ──
@router.post("/login", summary="Legacy telephone login endpoint")
def legacy_login(request: LoginRequest, db: Optional[Session] = Depends(get_db)):
    return send_otp(SendOTPRequest(identifier=request.phone, channel="phone"), db=db)
