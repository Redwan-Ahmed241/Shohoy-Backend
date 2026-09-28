from fastapi import APIRouter, HTTPException, status, Depends
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
    VolunteerSignupRequest
)
from database.connection import get_db
from database.repository import repo
from routers.deps import get_current_user, require_legacy_auth
from services.otp_service import otp_service
from services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["Authentication & Profile"])

# Sign-in normally happens in the browser with Supabase Auth; the backend then only needs
# GET /auth/me. Endpoints marked "legacy" are the older self-issued-token flow and stay
# disabled unless ALLOW_LEGACY_AUTH=true (used by the automated test suite).


# ── 1. SEND OTP (Exclusively Email via Resend) ──
@router.post(
    "/send-otp",
    dependencies=[Depends(require_legacy_auth)],
    response_model=SendOTPResponse,
    summary="Send verification OTP to user email via Resend"
)
def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """
    Dispatches a 6-digit security OTP code to the user's email address via Resend.
    - If API key is not configured, automatically logs the OTP and returns debug_otp in development.
    """
    clean_email = (request.email or request.identifier or "").strip().lower()

    # Check if user already exists
    existing_user = repo.get_user_by_email(db, clean_email)

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
    dependencies=[Depends(require_legacy_auth)],
    response_model=AuthResponse,
    summary="Verify Email OTP code and authenticate or advance to registration"
)
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
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
    user_data = repo.get_user_by_email(db, clean_email)

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
    dependencies=[Depends(require_legacy_auth)],
    summary="Register a new Public user / volunteer profile"
)
def register_public(request: PublicRegisterRequest, db: Session = Depends(get_db)):
    """
    Creates a minimal Public user profile:
    - First name, last name, phone, optional email
    - Skills (predefined + custom)
    - Equipment (predefined + custom)
    - Avatar, gender
    """
    # Check if user with this email already exists
    clean_email = request.email.strip().lower()
    existing = repo.get_user_by_email(db, clean_email)
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
        updated_user = repo.update_user(db, existing["id"], update_data) or existing

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

    created_user = repo.create_user(db, user_payload)

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
    dependencies=[Depends(require_legacy_auth)],
    summary="Register a Fieldworker profile with personal verification & certificates"
)
def register_fieldworker(request: FieldworkerRegisterRequest, db: Session = Depends(get_db)):
    """
    Creates a Fieldworker profile with personal verification details:
    - Same as public profile (name, phone, mail, skills, equipment, avatar, gender)
    - Plus: NID number, residential address, Date of Birth (DOB), and optional experience certificate.
    """
    clean_email = request.email.strip().lower()
    existing = repo.get_user_by_email(db, clean_email)
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
        updated_user = repo.update_user(db, existing["id"], update_data) or existing

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

    created_user = repo.create_user(db, user_payload)

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
def get_auth_options(db: Session = Depends(get_db)):
    """
    Returns lists of predefined skills and equipment tags to easily render multi-select chips/checklists,
    while allowing users to type custom additions.
    """
    return repo.get_auth_options()


# ── 6. CURRENT USER PROFILE ──
@router.get(
    "/me",
    response_model=AuthUser,
    summary="Get profile of currently logged-in user"
)
def read_current_user(current_user: AuthUser = Depends(get_current_user)):
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
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows updating profile fields including custom skills, equipment, address, avatar, etc.
    """
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        return current_user

    updated = repo.update_user(db, current_user.id, update_data)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update profile; user not found."
        )

    return AuthUser(**updated)


# ── 8. VOLUNTEER SIGN-UP (SIGNED-IN USER) ──
@router.post(
    "/register/volunteer",
    response_model=AuthUser,
    summary="Register the signed-in user as a field volunteer"
)
def register_volunteer(
    request: VolunteerSignupRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves volunteer details for the authenticated user. Public accounts become fieldworkers
    with verification pending; admins keep their role.
    """
    update_data = {
        "first_name": request.first_name.strip(),
        "last_name": request.last_name.strip(),
        "phone_number": (request.phone_number or "").strip() or current_user.phone_number,
        "skills": request.skills,
        "equipment": request.equipment,
    }
    if current_user.role == "public":
        update_data["role"] = "fieldworker"
        update_data["verification_status"] = "Pending"

    updated = repo.update_user(db, current_user.id, update_data)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to save volunteer details; user not found."
        )

    repo.update_volunteer_details(db, updated, request.district, request.skills)
    return AuthUser(**updated)


# ─── 9. DIRECT DATABASE LOGIN (LEGACY — REQUIRES ALLOW_LEGACY_AUTH) ───
@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Direct Database Authentication (legacy, disabled by default)",
    dependencies=[Depends(require_legacy_auth)],
)
def direct_login(request: LoginRequest, db: Session = Depends(get_db)):
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
    user_data = (
        repo.get_user_by_email(db, target)
        or repo.get_user_by_phone(db, target)
        or repo.get_user_by_identifier(db, target)
    )

    if user_data:
        req_role = (request.role or "").strip().lower()
        if req_role in ("admin", "volunteer", "fieldworker") and user_data.get("role") != req_role:
            db_role = "fieldworker" if req_role == "volunteer" else req_role
            updated = repo.update_user(db, user_data["id"], {"role": db_role})
            if updated:
                user_data = updated

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

    created_user = repo.create_user(db, user_payload)

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
