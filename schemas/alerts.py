from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict

SeverityLevel = Literal['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'ALL CLEAR']
VerificationStatus = Literal['Government Verified', 'Partner Verified', 'Unverified']

class FloodAlert(BaseModel):
    id: str
    severity: SeverityLevel
    type: str
    title: str
    description: str
    affectedAreas: List[str]
    issuedAt: str
    verificationStatus: VerificationStatus

    model_config = ConfigDict(populate_by_name=True)

class FloodAlertCreate(BaseModel):
    severity: SeverityLevel
    type: str
    title: str
    description: str
    affectedAreas: List[str]
    verificationStatus: Optional[VerificationStatus] = 'Unverified'
