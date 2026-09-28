from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from schemas.contacts import EmergencyContact
from database.connection import get_db
from database.repository import repo

router = APIRouter(prefix="/contacts", tags=["Emergency Directory"])

@router.get("", response_model=List[EmergencyContact], summary="Directory of emergency helplines & control rooms")
def get_contacts(
    category: Optional[str] = Query('All', description="Category e.g. National Emergency, Fire Service, Medical"),
    district: Optional[str] = Query('All Districts', description="Filter by district name or 'All Districts'"),
    db: Session = Depends(get_db)
):
    """Fetch verified emergency telephone numbers, hotlines, and DC control room contacts (public)."""
    return repo.get_contacts(db, category=category, district=district)
