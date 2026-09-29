from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

class VolunteerAssignment(BaseModel):
    id: str
    title: str
    location: str
    district: str
    durationHours: int
    teamSize: int
    priority: Literal['low', 'medium', 'high', 'critical']
    status: Literal['Available', 'Assigned', 'In Progress', 'Completed', 'Cancelled', 'Declined']
    requestId: Optional[str] = None
    assignedVolunteerId: Optional[str] = None
    assignedVolunteerName: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class VolunteerProfile(BaseModel):
    id: str
    name: str
    code: str  # e.g. VOL-1A2B3C4D
    district: str
    joinDate: str
    isAvailable: bool
    hoursLogged: float
    tasksCompleted: int
    rating: float
    currentAssignment: Optional[VolunteerAssignment] = None
    skills: List[str]
    dutyStatus: Literal['Off Duty', 'On Duty', 'Paused'] = 'Off Duty'
    checkedInAt: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class AssignmentCreatePayload(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    location: str = Field(..., min_length=1, max_length=255)
    district: str = Field(..., min_length=1, max_length=100)
    durationHours: int = Field(4, ge=1, le=72)
    teamSize: int = Field(4, ge=1, le=100)
    priority: Literal['low', 'medium', 'high', 'critical'] = 'high'

class CheckInPayload(BaseModel):
    status: Literal['Checked In', 'Paused', 'Completed'] = 'Checked In'

class AvailabilityPayload(BaseModel):
    isAvailable: bool

class VerificationUpdatePayload(BaseModel):
    status: Literal['Verified', 'Pending', 'Rejected']
