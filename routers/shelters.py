from typing import List, Optional, Dict
from fastapi import APIRouter, Query
from schemas.shelters import Shelter, ShelterSummaryStats, ShelterFilterParams
from database.repository import db

router = APIRouter(prefix="/shelters", tags=["Emergency Shelters"])

@router.get("", response_model=List[Shelter], summary="List all emergency shelters")
def get_shelters(
    status: Optional[str] = Query('All', description="Filter by status: Open, Nearly Full, Full, or All"),
    district: Optional[str] = Query('All', description="Filter by district name or All")
):
    """
    Retrieve shelters matching optional status and district filters.
    """
    return db.get_shelters(status=status, district=district)

@router.get("/summary", response_model=ShelterSummaryStats, summary="Get shelter aggregate metrics")
def get_shelter_summary():
    """
    Returns high-level shelter metrics: total, open, nearly full, and available free spaces.
    """
    return db.get_shelter_stats()

@router.post("/filter", response_model=List[Shelter], summary="Advanced filter with amenities")
def filter_shelters_by_amenities(params: ShelterFilterParams):
    """
    Filter shelters by status, district, and required amenities (e.g. drinkingWater, medicalSupport).
    """
    return db.get_shelters(status=params.status, district=params.district, amenities=params.amenities)
