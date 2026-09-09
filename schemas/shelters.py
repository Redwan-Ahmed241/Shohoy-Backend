from typing import Optional, Literal, Dict
from pydantic import BaseModel, ConfigDict

ShelterStatus = Literal['Open', 'Nearly Full', 'Full', 'Unverified']
RouteStatus = Literal['Route OK', 'Caution', 'Blocked']
ShelterCategory = Literal['Education Institution', 'Cyclone Shelter', 'Sports Facility', 'School', 'Government Building']

class ShelterAmenities(BaseModel):
    drinkingWater: bool = True
    toilets: bool = True
    womenToilets: bool = True
    electricity: bool = True
    generator: bool = False
    food: bool = True
    medicalSupport: bool = False

class Shelter(BaseModel):
    id: str
    name: str
    address: str
    upazila: str
    district: str
    occupancy: int
    capacity: int
    status: ShelterStatus
    routeStatus: RouteStatus
    category: ShelterCategory
    amenities: ShelterAmenities

    model_config = ConfigDict(populate_by_name=True)

class ShelterSummaryStats(BaseModel):
    totalShelters: int
    openShelters: int
    nearlyFull: int
    freeSpaces: str

class ShelterFilterParams(BaseModel):
    status: Optional[str] = 'All'
    district: Optional[str] = 'All'
    amenities: Optional[Dict[str, bool]] = None
