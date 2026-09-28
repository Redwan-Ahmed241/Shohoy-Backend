import re
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import config
from database.connection import get_db
from database.repository import repo, donation_to_dict
from schemas.donations import DonationInitRequest, DonationInitResponse, DonationStatus
from services.sslcommerz_service import sslcommerz_service

router = APIRouter(prefix="/donations", tags=["Donations"])


def _origin_allowed(origin: str) -> bool:
    """Same allowlist CORS uses — stops /init being used as an open redirect to a third-party site."""
    origin = origin.rstrip("/")
    return origin in {o.rstrip("/") for o in config.CORS_ORIGINS} or bool(re.match(config.CORS_ORIGIN_REGEX, origin))


async def _extract_fields(request: Request) -> Dict[str, Any]:
    """SSLCommerz calls these endpoints with GET query params (browser redirect) or a POST
    form body (IPN) depending on the callback — read whichever is present."""
    data = dict(request.query_params)
    if request.method == "POST":
        try:
            form = await request.form()
            data.update({k: str(v) for k, v in form.items()})
        except Exception:
            pass
    return data


@router.post("/init", response_model=DonationInitResponse, summary="Start a donation (opens an SSLCommerz payment session)")
async def init_donation(payload: DonationInitRequest, db: Session = Depends(get_db)):
    """Citizen donation flow. No account needed. Returns a real SSLCommerz gateway URL to redirect to."""
    if not _origin_allowed(payload.returnOrigin):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unrecognized return origin.")

    campaigns = {c["id"]: c for c in repo.get_campaigns(db)}
    campaign = campaigns.get(payload.campaignId)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")

    donation = repo.create_donation(
        db, payload.campaignId, payload.amount,
        payload.donorName, payload.donorEmail, payload.donorPhone, payload.returnOrigin
    )

    base = f"{config.BACKEND_PUBLIC_URL}{config.API_V1_PREFIX}/donations"
    try:
        session = await sslcommerz_service.create_session(
            tran_id=donation.tran_id,
            amount=payload.amount,
            campaign_title=campaign["title"],
            donor_name=payload.donorName,
            donor_email=payload.donorEmail,
            donor_phone=payload.donorPhone,
            success_url=f"{base}/success",
            fail_url=f"{base}/fail",
            cancel_url=f"{base}/cancel",
            ipn_url=f"{base}/ipn",
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach the payment gateway. Please try again.")

    if session.get("status") != "SUCCESS" or not session.get("GatewayPageURL"):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=session.get("failedreason") or "Payment gateway rejected the request.")

    return DonationInitResponse(gatewayUrl=session["GatewayPageURL"], tranId=donation.tran_id)


@router.get("/status/{tran_id}", response_model=DonationStatus, summary="Check a donation's current status")
def get_donation_status(tran_id: str, db: Session = Depends(get_db)):
    donation = repo.get_donation_by_tran_id(db, tran_id)
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found.")
    return donation_to_dict(donation)


async def _finalize_and_redirect(request: Request, db: Session, outcome: str) -> RedirectResponse:
    fields = await _extract_fields(request)
    tran_id = fields.get("tran_id", "")
    donation = repo.get_donation_by_tran_id(db, tran_id)
    return_origin = donation.return_origin if donation else config.CORS_ORIGINS[-1]

    if outcome == "Success" and donation:
        val_id = fields.get("val_id", "")
        try:
            result = await sslcommerz_service.validate_transaction(val_id) if val_id else {}
        except Exception:
            result = {}
        verified = result.get("status") in ("VALID", "VALIDATED") and float(result.get("amount", 0) or 0) >= donation.amount - 0.01
        repo.finalize_donation(
            db, tran_id, "Success" if verified else "Failed",
            val_id=val_id, bank_tran_id=fields.get("bank_tran_id"), card_type=result.get("card_type")
        )
        outcome = "Success" if verified else "Failed"
    elif donation:
        repo.finalize_donation(db, tran_id, outcome)

    path = {"Success": "/donate/success", "Failed": "/donate/fail", "Cancelled": "/donate/cancel"}[outcome]
    return RedirectResponse(url=f"{return_origin}{path}?tran_id={tran_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.api_route("/success", methods=["GET", "POST"], summary="[SSLCommerz callback] payment succeeded")
async def donation_success(request: Request, db: Session = Depends(get_db)):
    return await _finalize_and_redirect(request, db, "Success")


@router.api_route("/fail", methods=["GET", "POST"], summary="[SSLCommerz callback] payment failed")
async def donation_fail(request: Request, db: Session = Depends(get_db)):
    return await _finalize_and_redirect(request, db, "Failed")


@router.api_route("/cancel", methods=["GET", "POST"], summary="[SSLCommerz callback] donor cancelled")
async def donation_cancel(request: Request, db: Session = Depends(get_db)):
    return await _finalize_and_redirect(request, db, "Cancelled")


@router.post("/ipn", summary="[SSLCommerz callback] server-to-server payment notification")
async def donation_ipn(request: Request, db: Session = Depends(get_db)):
    """The reliable backup for /success — SSLCommerz calls this directly, so it works even if
    the donor closes their browser before the success redirect completes."""
    fields = await _extract_fields(request)
    tran_id = fields.get("tran_id", "")
    val_id = fields.get("val_id", "")
    donation = repo.get_donation_by_tran_id(db, tran_id)
    if not donation or not val_id:
        return {"received": True}

    try:
        result = await sslcommerz_service.validate_transaction(val_id)
    except Exception:
        return {"received": True}

    verified = result.get("status") in ("VALID", "VALIDATED") and float(result.get("amount", 0) or 0) >= donation.amount - 0.01
    if verified:
        repo.finalize_donation(db, tran_id, "Success", val_id=val_id, bank_tran_id=fields.get("bank_tran_id"), card_type=result.get("card_type"))
    return {"received": True}
