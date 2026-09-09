from typing import List, Optional
from fastapi import APIRouter, Query
from schemas.contacts import EmergencyContact
from database.repository import db

router = APIRouter(prefix="/contacts", tags=["Emergency Directory"])

@router.get("", response_model=List[EmergencyContact], summary="Directory of emergency helplines & control rooms")
def get_contacts(
    category: Optional[str] = Query('All', description="Category e.g. National Emergency, Fire Service, Medical"),
    district: Optional[str] = Query('All Districts', description="Filter by district name or 'All Districts'")
):
    """
    Fetch verified emergency telephone numbers, hotlines, and DC control room contacts.
    """
    return db.get_contacts(category=category, district=district)
