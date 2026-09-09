from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.campaigns import ReliefCampaign, CampaignSummaryStats
from database.connection import get_db
from database.supabase_repository import supabase_repo
from database.repository import db as mem_db

router = APIRouter(prefix="/campaigns", tags=["Relief Campaigns"])

@router.get("", response_model=List[ReliefCampaign], summary="List all verified relief campaigns")
def get_campaigns(db: Optional[Session] = Depends(get_db)):
    """Retrieve active NGO and government relief campaigns."""
    if db is not None:
        return supabase_repo.get_campaigns(db)
    return mem_db.get_campaigns()

@router.get("/summary", response_model=CampaignSummaryStats, summary="Get campaigns fundraising summary")
def get_campaign_summary(db: Optional[Session] = Depends(get_db)):
    """Aggregate statistics on active campaigns, households reached, and total raised funds in BDT."""
    if db is not None:
        return supabase_repo.get_campaign_stats(db)
    return mem_db.get_campaign_stats()
