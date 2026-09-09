from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

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
