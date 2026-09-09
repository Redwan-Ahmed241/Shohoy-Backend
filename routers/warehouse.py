from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from schemas.warehouse import WarehouseItem
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/warehouse", tags=["Logistics & Warehouse"])

@router.get("/inventory", response_model=List[WarehouseItem], summary="List warehouse inventory")
def get_inventory(
    category: Optional[str] = Query('All', description="Category filter e.g. Food, Water, Medicine"),
    db: Optional[Session] = Depends(get_db)
):
    """Retrieve stock quantities across relief warehouses."""
    if db is not None:
        return supabase_repo.get_warehouse_inventory(db, category=category)
    return mem_db.get_warehouse_inventory(category=category)

@router.get("/alerts/low-stock", response_model=List[WarehouseItem], summary="Get low-stock warehouse alerts")
def get_low_stock(db: Optional[Session] = Depends(get_db)):
    """Returns inventory items with status 'LOW' requiring restocking."""
    if db is not None:
        return supabase_repo.get_low_stock_items(db)
    return mem_db.get_low_stock_items()

@router.get("/alerts/expiring", response_model=List[WarehouseItem], summary="Get items nearing expiry")
def get_expiring_items(db: Optional[Session] = Depends(get_db)):
    """Returns perishable or medical supplies with an expiry date."""
    if db is not None:
        return supabase_repo.get_expiring_items(db)
    return mem_db.get_expiring_items()
