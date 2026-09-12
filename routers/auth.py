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


# ── 1. SEND OTP (Exclusively Email via Resend) ──
@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send verification OTP to user email via Resend"
)
def send_otp(request: SendOTPRequest, db: Optional[Session] = Depends(get_db)):
    """
    Dispatches a 6-digit security OTP code to the user's email address via Resend.
    - If API key is not configured, automatically logs the OTP and returns debug_otp in development.
    """
    clean_email = (request.email or request.identifier or "").strip().lower()

    # Check if user already exists
    if db is not None:
        existing_user = supabase_repo.get_user_by_email(db, clean_email)
    else:
        existing_user = mem_db.get_user_by_email(clean_email)

    is_new = (existing_user is None)

    # Generate 6-digit OTP code
    otp = otp_service.generate_otp(clean_email, channel="email")

    # Dispatch via Resend Email
    dispatch_result = email_service.send_otp_email(clean_email, otp)

    # In development or if delivery is restricted by sandbox, surface OTP for developer convenience
    is_dev = config.ENVIRONMENT in ("development", "test")
    delivered = dispatch_result.get("success", False)
    debug_otp = otp if is_dev or not delivered else None

    if delivered:
        msg = f"OTP successfully dispatched to {clean_email} via Resend."
    else:
        msg = f"Verification code generated. Use code '{otp}' to test sign-in in development."

    return SendOTPResponse(
        success=True,
        email=clean_email,
        is_new_user=is_new,
        message=msg,
        debug_otp=debug_otp
    )



# ── 2. VERIFY OTP ──
@router.post(
    "/verify-otp",
    response_model=AuthResponse,
    summary="Verify Email OTP code and authenticate or advance to registration"
)
def verify_otp(request: VerifyOTPRequest, db: Optional[Session] = Depends(get_db)):
    """
    Validates the 6-digit OTP received via email:
    - If user exists: Issues persistent session bearer token and returns profile.
    - If user is new: Returns a temporary verification ticket to complete registration.
    """
    clean_email = (request.email or request.identifier or "").strip().lower()
    is_valid, msg = otp_service.verify_otp(clean_email, request.otp)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # Find existing account by email
    if db is not None:
        user_data = supabase_repo.get_user_by_email(db, clean_email)
    else:
        user_data = mem_db.get_user_by_email(clean_email)

    if user_data:
        token = otp_service.create_token({
            "sub": user_data["id"],
            "role": user_data.get("role", "public"),
            "email": user_data.get("email"),
            "phone": user_data.get("phoneNumber") or user_data.get("phone_number")
        })
        otp_service.clear_otp(clean_email)
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
            "sub": clean_email,
            "scope": "registration"
        }, expire_days=1)

        return AuthResponse(
            success=True,
            is_new_user=True,
            user=None,
            token=None,
            verification_ticket=ticket,
            message="Email OTP verified successfully. Please complete your registration profile."
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
    # Check if user with this email already exists
    clean_email = request.email.strip().lower()
    existing = supabase_repo.get_user_by_email(db, clean_email) if db is not None else mem_db.get_user_by_email(clean_email)
    if existing:
        update_data = {
            "first_name": request.first_name.strip(),
            "last_name": request.last_name.strip(),
            "phone_number": request.phone_number.strip() if request.phone_number else existing.get("phone_number"),
            "skills": request.skills or existing.get("skills", []),
            "equipment": request.equipment or existing.get("equipment", []),
            "gender": request.gender or existing.get("gender"),
            "avatar": request.avatar or existing.get("avatar")
        }
        if db is not None:
            updated_user = supabase_repo.update_user(db, existing["id"], update_data) or existing
        else:
            updated_user = mem_db.update_user(existing["id"], update_data) or existing

        token = otp_service.create_token({
            "sub": updated_user["id"],
            "role": updated_user.get("role", "public"),
            "email": updated_user.get("email"),
            "phone": updated_user.get("phoneNumber") or updated_user.get("phone_number")
        })
        return AuthResponse(
            success=True,
            is_new_user=False,
            user=AuthUser(**updated_user),
            token=token,
            message="Profile updated and signed in successfully."
        )

    avatar_url = request.avatar or f"https://api.dicebear.com/7.x/initials/svg?seed={request.first_name}+{request.last_name}"

    user_payload = {
        "role": "public",
        "first_name": request.first_name.strip(),
        "last_name": request.last_name.strip(),
        "phone_number": request.phone_number.strip() if request.phone_number else None,
        "email": clean_email,
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
        "email": created_user.get("email"),
        "phone": created_user.get("phoneNumber") or created_user.get("phone_number")
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
    clean_email = request.email.strip().lower()
    existing = supabase_repo.get_user_by_email(db, clean_email) if db is not None else mem_db.get_user_by_email(clean_email)
    if existing:
        update_data = {
            "first_name": request.first_name.strip(),
            "last_name": request.last_name.strip(),
            "phone_number": request.phone_number.strip() if request.phone_number else existing.get("phone_number"),
            "skills": request.skills or existing.get("skills", []),
            "equipment": request.equipment or existing.get("equipment", []),
            "gender": request.gender or existing.get("gender"),
            "avatar": request.avatar or existing.get("avatar")
        }
        if db is not None:
            updated_user = supabase_repo.update_user(db, existing["id"], update_data) or existing
        else:
            updated_user = mem_db.update_user(existing["id"], update_data) or existing

        token = otp_service.create_token({
            "sub": updated_user["id"],
            "role": updated_user.get("role", "public"),
            "email": updated_user.get("email"),
            "phone": updated_user.get("phoneNumber") or updated_user.get("phone_number")
        })
        return AuthResponse(
            success=True,
            is_new_user=False,
            user=AuthUser(**updated_user),
            token=token,
            message="Profile updated and signed in successfully."
        )

    avatar_url = request.avatar or f"https://api.dicebear.com/7.x/initials/svg?seed={request.first_name}+{request.last_name}"

    user_payload = {
        "role": "fieldworker",
        "first_name": request.first_name.strip(),
        "last_name": request.last_name.strip(),
        "phone_number": request.phone_number.strip() if request.phone_number else None,
        "email": clean_email,
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



# ─── 8. DIRECT DATABASE LOGIN (NO VERIFICATION BARRIER) ───
@router.post("/login", response_model=AuthResponse, summary="Direct Database Authentication")
def direct_login(request: LoginRequest, db: Optional[Session] = Depends(get_db)):
    """
    Authenticates directly against the database with zero OTP/email verification barriers.
    - If user exists in DB: Returns user profile and persistent JWT token.
    - If user does NOT exist: Automatically provisions the user in the database with the requested role.
    """
    target = (request.email or request.phone or request.identifier or "").strip().lower()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an email or mobile number to sign in."
        )

    # Search in database by email, phone, or identifier
    user_data = None
    if db is not None:
        user_data = (
            supabase_repo.get_user_by_email(db, target)
            or supabase_repo.get_user_by_phone(db, target)
            or supabase_repo.get_user_by_identifier(db, target)
        )
    else:
        user_data = (
            mem_db.get_user_by_email(target)
            or mem_db.get_user_by_phone(target)
            or mem_db.get_user_by_identifier(target)
        )

    if user_data:
        req_role = (request.role or "").strip().lower()
        if req_role in ("admin", "volunteer", "fieldworker") and user_data.get("role") != req_role:
            db_role = "fieldworker" if req_role == "volunteer" else req_role
            if db is not None:
                updated = supabase_repo.update_user(db, user_data["id"], {"role": db_role})
                if updated:
                    user_data = updated
            else:
                user_data["role"] = db_role

        token = otp_service.create_token({
            "sub": user_data["id"],
            "role": user_data.get("role", "public"),
            "email": user_data.get("email"),
            "phone": user_data.get("phoneNumber") or user_data.get("phone_number")
        })

        return AuthResponse(
            success=True,
            is_new_user=False,
            user=AuthUser(**user_data),
            token=token,
            message="Sign in successful. Welcome to Shohay."
        )

    # If user does not exist, provision in DB
    is_email = "@" in target
    email_val = target if is_email else None
    phone_val = target if not is_email else None

    chosen_role = (request.role or "public").strip().lower()
    if chosen_role in ("volunteer", "fieldworker"):
        db_role = "fieldworker"
        def_first, def_last = "Field", "Volunteer"
    elif chosen_role == "admin":
        db_role = "admin"
        def_first, def_last = "District", "Coordinator"
    else:
        db_role = "public"
        def_first, def_last = "Public", "Citizen"

    if request.name:
        parts = request.name.strip().split(" ", 1)
        def_first = parts[0]
        def_last = parts[1] if len(parts) > 1 else ""

    avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={def_first}+{def_last}"

    user_payload = {
        "role": db_role,
        "first_name": def_first,
        "last_name": def_last,
        "phone_number": phone_val,
        "email": email_val,
        "avatar": avatar_url,
        "gender": "Other",
        "skills": ["First Aid & CPR", "Food & Relief Distribution"] if db_role in ("fieldworker", "admin") else [],
        "equipment": ["Life Jackets & Buoys"] if db_role in ("fieldworker", "admin") else [],
        "nid_number": None,
        "address": "Bangladesh",
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
        "role": created_user.get("role", db_role),
        "email": created_user.get("email"),
        "phone": created_user.get("phoneNumber") or created_user.get("phone_number")
    })

    return AuthResponse(
        success=True,
        is_new_user=True,
        user=AuthUser(**created_user),
        token=token,
        message="Account created and signed in successfully."
    )
