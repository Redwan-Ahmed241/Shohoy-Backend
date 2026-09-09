from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict

class VolunteerAssignment(BaseModel):
    id: str
    title: str
    location: str
    district: str
    durationHours: int
    teamSize: int
    priority: Literal['low', 'medium', 'high', 'critical']
    status: Literal['Available', 'Assigned', 'In Progress', 'Completed']

    model_config = ConfigDict(populate_by_name=True)

class VolunteerProfile(BaseModel):
    id: str
    name: str
    code: str  # e.g. VOL-2024-DEMO
    district: str
    joinDate: str
    isAvailable: bool
    hoursLogged: int
    tasksCompleted: int
    rating: float
    currentAssignment: Optional[VolunteerAssignment] = None
    skills: List[str]

    model_config = ConfigDict(populate_by_name=True)
