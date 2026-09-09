from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

UserRole = Literal['public', 'volunteer', 'admin']

class AuthUser(BaseModel):
    id: str
    name: str
    role: UserRole
    phone: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class LoginRequest(BaseModel):
    phone: str
    role: UserRole = 'public'

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str
    role: UserRole = 'public'

class AuthResponse(BaseModel):
    user: AuthUser
    token: str
    message: str
