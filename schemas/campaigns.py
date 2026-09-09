from typing import List, Literal
from pydantic import BaseModel, ConfigDict
from .alerts import VerificationStatus

class ReliefCampaign(BaseModel):
    id: str
    title: str
    organization: str
    district: str
    coverageAreas: List[str]
    targetAmount: float
    raisedAmount: float
    householdsTarget: int
    householdsReached: int
    verificationStatus: VerificationStatus

    model_config = ConfigDict(populate_by_name=True)

class CampaignSummaryStats(BaseModel):
    activeCampaigns: int
    householdsReached: str
    totalRaisedBDT: str
