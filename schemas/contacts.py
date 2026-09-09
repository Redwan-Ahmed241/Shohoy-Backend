from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

ContactCategory = Literal[
    'National Emergency',
    'Fire Service',
    'Medical',
    'Disaster Management',
    'District Control Room',
    'Protection',
    'Platform Hotline',
    'Rescue',
    'Hospital'
]

class EmergencyContact(BaseModel):
    id: str
    title: str
    category: ContactCategory
    district: Optional[str] = None
    phone: str
    description: str
    availability: str
    isTollFree: Optional[bool] = False
    isVerified: Optional[bool] = True
    notes: Optional[str] = None
    lastVerified: str

    model_config = ConfigDict(populate_by_name=True)
