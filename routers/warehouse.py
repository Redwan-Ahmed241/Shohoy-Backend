from typing import List, Optional
from fastapi import APIRouter, Query
from schemas.warehouse import WarehouseItem
from database.repository import db

router = APIRouter(prefix="/warehouse", tags=["Logistics & Warehouse"])

@router.get("/inventory", response_model=List[WarehouseItem], summary="List warehouse inventory")
def get_inventory(category: Optional[str] = Query('All', description="Category filter e.g. Food, Water, Medicine")):
    """
    Retrieve stock quantities across relief warehouses.
    """
    return db.get_warehouse_inventory(category=category)

@router.get("/alerts/low-stock", response_model=List[WarehouseItem], summary="Get low-stock warehouse alerts")
def get_low_stock():
    """
    Returns inventory items with status 'LOW' requiring restocking.
    """
    return db.get_low_stock_items()

@router.get("/alerts/expiring", response_model=List[WarehouseItem], summary="Get items nearing expiry")
def get_expiring_items():
    """
    Returns perishable or medical supplies with an expiry date.
    """
    return db.get_expiring_items()
