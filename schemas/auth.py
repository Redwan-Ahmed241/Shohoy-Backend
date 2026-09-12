from typing import Optional, List, Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

UserRole = Literal["public", "fieldworker", "admin", "volunteer"]

class SendOTPRequest(BaseModel):
    """
    Step 1: Request OTP via Email (Resend).
    """
    email: Optional[str] = Field(None, description="User email address for OTP delivery")
    identifier: Optional[str] = Field(None, description="Email alias for backwards compatibility")

    @model_validator(mode="after")
    def validate_email(self):
        target = (self.email or self.identifier or "").strip().lower()
        if not target:
            raise ValueError("Email address is required to receive verification OTP.")
        if "@" not in target:
            raise ValueError("Please provide a valid email address.")
        self.email = target
        self.identifier = target
        return self

class SendOTPResponse(BaseModel):
    success: bool
    email: str
    is_new_user: bool
    message: str
    debug_otp: Optional[str] = Field(None, description="Available in development mode for easy testing")

class VerifyOTPRequest(BaseModel):
    """
    Step 2: Validate the 6-digit OTP received via Email.
    """
    email: Optional[str] = Field(None, description="Email address that received the OTP")
    identifier: Optional[str] = Field(None, description="Email alias for backwards compatibility")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @model_validator(mode="after")
    def validate_email(self):
        target = (self.email or self.identifier or "").strip().lower()
        if not target:
            raise ValueError("Email address is required for OTP verification.")
        self.email = target
        self.identifier = target
        return self

class PublicRegisterRequest(BaseModel):
    """
    Profile registration for Public users / volunteers.
    Minimal, frictionless data entry with email-based authentication.
    """
    email: str = Field(..., min_length=3, max_length=255, description="User email address (used for login)")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's given first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's family surname")
    phone_number: Optional[str] = Field(None, description="Optional contact phone number")
    skills: List[str] = Field(default_factory=list, description="Selected predefined skills plus user's custom skills")
    equipment: List[str] = Field(default_factory=list, description="Available rescue/relief equipment items")
    avatar: Optional[str] = Field(None, description="Avatar image URL")
    gender: Optional[str] = Field(None, description="Gender (e.g. Male, Female, Other, Prefer not to say)")

    @model_validator(mode="after")
    def validate_email_format(self):
        target = self.email.strip().lower()
        if "@" not in target:
            raise ValueError("Please provide a valid email address.")
        self.email = target
        return self

class FieldworkerRegisterRequest(BaseModel):
    """
    Profile registration for Fieldworkers.
    Includes personal verification (NID, address, gender, DOB) and experience certificates.
    """
    email: str = Field(..., min_length=3, max_length=255, description="Fieldworker email address (used for login)")
    first_name: str = Field(..., min_length=1, max_length=100, description="Fieldworker's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Fieldworker's last name")
    phone_number: Optional[str] = Field(None, description="Optional contact phone number")
    skills: List[str] = Field(default_factory=list, description="Predefined and custom skills")
    equipment: List[str] = Field(default_factory=list, description="Equipments available with fieldworker")
    avatar: Optional[str] = Field(None, description="Profile avatar URL")
    gender: str = Field(..., description="Gender (e.g. Male, Female, Other)")
    
    # Personal verification fields
    nid_number: str = Field(..., min_length=10, max_length=50, description="National ID (NID) number for verification")
    address: str = Field(..., min_length=5, max_length=500, description="Current residential or field station address")
    dob: str = Field(..., description="Date of Birth (YYYY-MM-DD)")
    experience_certificate: Optional[str] = Field(None, description="URL or description of certified training / rescue credentials")

    @model_validator(mode="after")
    def validate_email_format(self):
        target = self.email.strip().lower()
        if "@" not in target:
            raise ValueError("Please provide a valid email address.")
        self.email = target
        return self


class AuthUser(BaseModel):
    id: str
    role: str
    first_name: str
    last_name: str
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    nid_number: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    experience_certificate: Optional[str] = None
    verification_status: Optional[str] = "Pending"
    created_at: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def populate_names(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "first_name" not in data and "firstName" in data:
                data["first_name"] = data["firstName"]
            if "last_name" not in data and "lastName" in data:
                data["last_name"] = data["lastName"]
            if "phone_number" not in data and "phoneNumber" in data:
                data["phone_number"] = data["phoneNumber"]
            if "nid_number" not in data and "nidNumber" in data:
                data["nid_number"] = data["nidNumber"]
            if "experience_certificate" not in data and "experienceCertificate" in data:
                data["experience_certificate"] = data["experienceCertificate"]
            if "verification_status" not in data and "verificationStatus" in data:
                data["verification_status"] = data["verificationStatus"]
        return data

    @model_validator(mode="after")
    def set_computed_name(self):
        if not self.name and self.first_name and self.last_name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        return self


class AuthResponse(BaseModel):
    success: bool = True
    is_new_user: bool = False
    user: Optional[AuthUser] = None
    token: Optional[str] = None
    verification_ticket: Optional[str] = None
    message: str

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    skills: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    address: Optional[str] = None
    experience_certificate: Optional[str] = None

class AuthOptionsResponse(BaseModel):
    skills: List[str]
    equipment: List[str]
    genders: List[str]
    roles: List[str]

# Backwards compatibility models
class LoginRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    identifier: Optional[str] = None
    role: Optional[str] = "public"
    name: Optional[str] = None

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str
    role: UserRole = "public"
