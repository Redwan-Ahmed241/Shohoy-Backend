from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from schemas.contacts import EmergencyContact
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/contacts", tags=["Emergency Directory"])

@router.get("", response_model=List[EmergencyContact], summary="Directory of emergency helplines & control rooms")
def get_contacts(
    category: Optional[str] = Query('All', description="Category e.g. National Emergency, Fire Service, Medical"),
    district: Optional[str] = Query('All Districts', description="Filter by district name or 'All Districts'"),
    db: Optional[Session] = Depends(get_db)
):
    """Fetch verified emergency telephone numbers, hotlines, and DC control room contacts."""
    if db is not None:
        return supabase_repo.get_contacts(db, category=category, district=district)
    return mem_db.get_contacts(category=category, district=district)
