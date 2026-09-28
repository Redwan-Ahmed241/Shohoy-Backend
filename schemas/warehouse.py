from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

InventoryCategory = Literal['Food', 'Water', 'Medicine', 'Hygiene', 'Rescue Equipment', 'Shelter']
InventoryStatus = Literal['OK', 'LOW', 'CAUTION', 'EXPIRED']

class WarehouseItem(BaseModel):
    id: str
    sku: str
    name: str
    category: InventoryCategory
    availableCount: int
    unit: str
    reservedCount: int
    minStockThreshold: int
    status: InventoryStatus
    expiryDate: Optional[str] = None
    warehouseName: str
    lastCountDate: str

    model_config = ConfigDict(populate_by_name=True)

class StockMovementPayload(BaseModel):
    """Stock received into (receive) or sent out of (dispatch) a warehouse item."""
    itemId: str
    quantity: int = Field(..., ge=1, le=1_000_000)
    fromTo: str = Field(..., min_length=1, max_length=255, description="e.g. 'WFP donor -> Sylhet Central'")
    reference: Optional[str] = Field(None, max_length=100, description="PO, donation or request reference")
    notes: Optional[str] = Field(None, max_length=500)

class StockMovement(BaseModel):
    id: str
    itemId: str
    item: str
    type: Literal['INBOUND', 'DISPATCH']
    quantity: int
    qty: str
    fromTo: str
    ref: str
    notes: Optional[str] = None
    date: str

class StockMovementResult(BaseModel):
    item: WarehouseItem
    movement: StockMovement
