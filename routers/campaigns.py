from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.campaigns import ReliefCampaign, CampaignSummaryStats
from database.connection import get_db
from database.repository import repo

router = APIRouter(prefix="/campaigns", tags=["Relief Campaigns"])

@router.get("", response_model=List[ReliefCampaign], summary="List all verified relief campaigns")
def get_campaigns(db: Session = Depends(get_db)):
    """Retrieve active NGO and government relief campaigns (public)."""
    return repo.get_campaigns(db)

@router.get("/summary", response_model=CampaignSummaryStats, summary="Get campaigns fundraising summary")
def get_campaign_summary(db: Session = Depends(get_db)):
    """Aggregate statistics on active campaigns, households reached, and total raised funds in BDT."""
    return repo.get_campaign_stats(db)
