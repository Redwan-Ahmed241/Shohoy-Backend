from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

AssistanceType = Literal[
    'rescue', 'shelter', 'food', 'water', 'medicine', 'medical_emergency',
    'maternal', 'child_welfare', 'disability', 'hygiene', 'missing_person',
    'evacuation', 'other'
]

class VulnerableCount(BaseModel):
    children: int = 0
    elderly: int = 0
    pregnant: int = 0
    disabled: int = 0

class Location(BaseModel):
    district: str
    upazila: str
    union: str
    address: str
    landmark: Optional[str] = None
    gpsCoords: Optional[str] = None

class Contact(BaseModel):
    name: str
    phone: str
    altPhone: Optional[str] = None
    isAnonymous: bool = False

class AssistanceRequestPayload(BaseModel):
    types: List[AssistanceType]
    householdSize: int = Field(gt=0, description='Total members in household')
    vulnerableCount: VulnerableCount
    location: Location
    contact: Contact
    notes: Optional[str] = None

class AssistanceRequestRecord(AssistanceRequestPayload):
    id: str
    trackingId: str  # Format: SHY-2024-XXXXX
    status: Literal['Pending', 'Verified', 'Assigned', 'In Progress', 'Resolved'] = 'Pending'
    createdAt: str

    model_config = ConfigDict(populate_by_name=True)
