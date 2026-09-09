from fastapi import APIRouter
from schemas.auth import LoginRequest, OTPVerifyRequest, AuthResponse, AuthUser

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", summary="Request OTP for telephone authentication")
def login(request: LoginRequest):
    """
    Step 1 of phone-based login. Dispatches OTP (mocked: '123456').
    """
    return {
        "success": True,
        "phone": request.phone,
        "role": request.role,
        "message": "OTP sent successfully. Use '123456' for local testing."
    }

@router.post("/verify-otp", response_model=AuthResponse, summary="Verify OTP and receive session token")
def verify_otp(request: OTPVerifyRequest):
    """
    Step 2 of phone-based login. Validates OTP and creates user session.
    """
    user_name = "Field Officer" if request.role == "admin" else ("Volunteer Leader" if request.role == "volunteer" else "Citizen User")
    user = AuthUser(
        id=f"usr-{request.role}-001",
        name=user_name,
        role=request.role,
        phone=request.phone
    )
    return AuthResponse(
        user=user,
        token=f"shohay-token-{request.role}-{request.phone}",
        message="Authentication successful"
    )

@router.get("/me", response_model=AuthUser, summary="Get current logged-in user")
def get_current_user():
    """
    Returns the authenticated session user details.
    """
    return AuthUser(
        id="usr-demo-001",
        name="Demo Volunteer",
        role="volunteer",
        phone="01712345678"
    )
