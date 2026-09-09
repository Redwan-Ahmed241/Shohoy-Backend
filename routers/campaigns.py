from typing import List
from fastapi import APIRouter
from schemas.campaigns import ReliefCampaign, CampaignSummaryStats
from database.repository import db

router = APIRouter(prefix="/campaigns", tags=["Relief Campaigns"])

@router.get("", response_model=List[ReliefCampaign], summary="List all verified relief campaigns")
def get_campaigns():
    """
    Retrieve active NGO and government relief campaigns.
    """
    return db.get_campaigns()

@router.get("/summary", response_model=CampaignSummaryStats, summary="Get campaigns fundraising summary")
def get_campaign_summary():
    """
    Aggregate statistics on active campaigns, households reached, and total raised funds in BDT.
    """
    return db.get_campaign_stats()
