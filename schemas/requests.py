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

RequestStatus = Literal['Pending', 'Verified', 'Assigned', 'In Progress', 'Resolved']

class RequestTask(BaseModel):
    """The volunteer task dispatched for a request (coordinator view)."""
    id: str
    status: str
    assignedVolunteerName: Optional[str] = None

class AssistanceRequestAdminRecord(AssistanceRequestRecord):
    task: Optional[RequestTask] = None

class AssistanceRequestTracking(BaseModel):
    """What anyone with a tracking ID may see: progress only, no personal details."""
    trackingId: str
    types: List[str]
    status: str
    district: str = ''
    upazila: str = ''
    createdAt: str
    taskStatus: Optional[str] = None

class RequestStatusUpdate(BaseModel):
    status: RequestStatus
    notes: Optional[str] = Field(None, max_length=500)

class DispatchPayload(BaseModel):
    """Volunteer task created from a citizen request."""
    title: str = Field(..., min_length=3, max_length=500)
    location: str = Field(..., min_length=1, max_length=255)
    district: str = Field(..., min_length=1, max_length=100)
    durationHours: int = Field(4, ge=1, le=72)
    teamSize: int = Field(4, ge=1, le=100)
    priority: Literal['low', 'medium', 'high', 'critical'] = 'high'
