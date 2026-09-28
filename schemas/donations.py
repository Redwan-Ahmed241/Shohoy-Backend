from typing import Optional
from pydantic import BaseModel, Field


class DonationInitRequest(BaseModel):
    campaignId: str
    amount: float = Field(..., ge=10, le=500000, description="BDT, SSLCommerz sandbox range 10-500000")
    donorName: str = Field(..., min_length=2, max_length=255)
    donorEmail: str = Field(..., min_length=5, max_length=255)
    donorPhone: str = Field(..., min_length=6, max_length=50)
    returnOrigin: str = Field(..., description="Frontend origin to send the donor back to, e.g. https://shohay-bd.vercel.app")


class DonationInitResponse(BaseModel):
    gatewayUrl: str
    tranId: str


class DonationStatus(BaseModel):
    tranId: str
    status: str
    amount: float
    currency: str
    campaignId: str
    donorName: str
    createdAt: Optional[str] = None
    validatedAt: Optional[str] = None
