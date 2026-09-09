from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from schemas.shelters import Shelter, ShelterSummaryStats, ShelterFilterParams
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/shelters", tags=["Emergency Shelters"])

@router.get("", response_model=List[Shelter], summary="List all emergency shelters")
def get_shelters(
    status: Optional[str] = Query('All', description="Filter by status: Open, Nearly Full, Full, or All"),
    district: Optional[str] = Query('All', description="Filter by district name or All"),
    db: Optional[Session] = Depends(get_db)
):
    """Retrieve shelters matching optional status and district filters."""
    if db is not None:
        return supabase_repo.get_shelters(db, status=status, district=district)
    return mem_db.get_shelters(status=status, district=district)

@router.get("/summary", response_model=ShelterSummaryStats, summary="Get shelter aggregate metrics")
def get_shelter_summary(db: Optional[Session] = Depends(get_db)):
    """Returns high-level shelter metrics: total, open, nearly full, and available free spaces."""
    if db is not None:
        return supabase_repo.get_shelter_stats(db)
    return mem_db.get_shelter_stats()

@router.post("/filter", response_model=List[Shelter], summary="Advanced filter with amenities")
def filter_shelters_by_amenities(params: ShelterFilterParams, db: Optional[Session] = Depends(get_db)):
    """Filter shelters by status, district, and required amenities (e.g. drinkingWater, medicalSupport)."""
    if db is not None:
        return supabase_repo.get_shelters(db, status=params.status, district=params.district, amenities=params.amenities)
    return mem_db.get_shelters(status=params.status, district=params.district, amenities=params.amenities)
