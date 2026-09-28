from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from schemas.auth import AuthUser
from schemas.warehouse import WarehouseItem, StockMovement, StockMovementPayload, StockMovementResult
from database.connection import get_db
from database.repository import repo
from routers.deps import require_roles, repository_errors

router = APIRouter(prefix="/warehouse", tags=["Logistics & Warehouse"])

coordinator = require_roles("admin")


@router.get("/inventory", response_model=List[WarehouseItem], summary="List warehouse inventory", dependencies=[Depends(coordinator)])
def get_inventory(
    category: Optional[str] = Query('All', description="Category filter e.g. Food, Water, Medicine"),
    db: Session = Depends(get_db)
):
    """Retrieve stock quantities across relief warehouses."""
    return repo.get_warehouse_inventory(db, category=category)

@router.get("/alerts/low-stock", response_model=List[WarehouseItem], summary="Get low-stock warehouse alerts", dependencies=[Depends(coordinator)])
def get_low_stock(db: Session = Depends(get_db)):
    """Returns inventory items with status 'LOW' requiring restocking."""
    return repo.get_low_stock_items(db)

@router.get("/alerts/expiring", response_model=List[WarehouseItem], summary="Get items nearing expiry", dependencies=[Depends(coordinator)])
def get_expiring_items(db: Session = Depends(get_db)):
    """Returns perishable or medical supplies with an expiry date."""
    return repo.get_expiring_items(db)

@router.get("/movements", response_model=List[StockMovement], summary="Recent stock movements", dependencies=[Depends(coordinator)])
def get_movements(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    return repo.get_stock_movements(db, limit=limit)


def _move_stock(movement_type: str, payload: StockMovementPayload, user: AuthUser, db: Session):
    with repository_errors():
        result = repo.record_stock_movement(
            db, payload.itemId, movement_type, payload.quantity,
            payload.fromTo, payload.reference, payload.notes, user.id,
        )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item '{payload.itemId}' not found.")
    return result

@router.post("/receive", response_model=StockMovementResult, summary="Receive stock into a warehouse")
def receive_stock(payload: StockMovementPayload, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    """Adds stock, recalculates the OK / CAUTION / LOW status and logs an INBOUND movement."""
    return _move_stock("INBOUND", payload, user, db)

@router.post("/dispatch", response_model=StockMovementResult, summary="Dispatch stock out of a warehouse")
def dispatch_stock(payload: StockMovementPayload, user: AuthUser = Depends(coordinator), db: Session = Depends(get_db)):
    """Removes stock (409 if not enough) and logs a DISPATCH movement."""
    return _move_stock("DISPATCH", payload, user, db)
