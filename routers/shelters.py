from typing import List, Optional
from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.orm import Session
from schemas.shelters import Shelter, ShelterSummaryStats, ShelterFilterParams, ShelterCreate
from database.connection import get_db
from database.repository import repo
from routers.deps import require_roles

router = APIRouter(prefix="/shelters", tags=["Emergency Shelters"])

@router.get("", response_model=List[Shelter], summary="List all emergency shelters")
def get_shelters(
    status: Optional[str] = Query('All', description="Filter by status: Open, Nearly Full, Full, or All"),
    district: Optional[str] = Query('All', description="Filter by district name or All"),
    db: Session = Depends(get_db)
):
    """Retrieve shelters matching optional status and district filters (public)."""
    return repo.get_shelters(db, status=status, district=district)

@router.get("/summary", response_model=ShelterSummaryStats, summary="Get shelter aggregate metrics")
def get_shelter_summary(db: Session = Depends(get_db)):
    """Returns high-level shelter metrics: total, open, nearly full, and available free spaces."""
    return repo.get_shelter_stats(db)

@router.post("/filter", response_model=List[Shelter], summary="Advanced filter with amenities")
def filter_shelters_by_amenities(params: ShelterFilterParams, db: Session = Depends(get_db)):
    """Filter shelters by status, district, and required amenities (e.g. drinkingWater, medicalSupport)."""
    return repo.get_shelters(db, status=params.status, district=params.district, amenities=params.amenities)

@router.post(
    "",
    response_model=Shelter,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new emergency shelter (coordinators)",
    dependencies=[Depends(require_roles("admin"))],
)
def create_shelter(payload: ShelterCreate, db: Session = Depends(get_db)):
    """Add a verified shelter location to the public directory."""
    return repo.create_shelter(db, payload.model_dump())
