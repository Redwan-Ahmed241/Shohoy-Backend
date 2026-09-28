"""
SSLCommerz hosted-checkout integration (sandbox by default, same API shape as live).
Docs: https://developer.sslcommerz.com/doc/v4/
"""
from typing import Any, Dict

import httpx

import config

SESSION_URL = f"{config.SSLCOMMERZ_BASE_URL}/gwprocess/v4/api.php"
VALIDATION_URL = f"{config.SSLCOMMERZ_BASE_URL}/validator/api/validationserverAPI.php"


class SSLCommerzService:
    async def create_session(
        self,
        *,
        tran_id: str,
        amount: float,
        campaign_title: str,
        donor_name: str,
        donor_email: str,
        donor_phone: str,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        ipn_url: str,
    ) -> Dict[str, Any]:
        """Opens a payment session and returns SSLCommerz's response, including GatewayPageURL."""
        payload = {
            "store_id": config.SSLCOMMERZ_STORE_ID,
            "store_passwd": config.SSLCOMMERZ_STORE_PASSWORD,
            "total_amount": f"{amount:.2f}",
            "currency": "BDT",
            "tran_id": tran_id,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "ipn_url": ipn_url,
            "product_category": "Donation",
            "product_name": campaign_title[:100],
            "product_profile": "non-physical-goods",
            "shipping_method": "NO",
            "cus_name": donor_name,
            "cus_email": donor_email,
            "cus_phone": donor_phone,
            "cus_add1": "N/A",
            "cus_city": "Dhaka",
            "cus_postcode": "1000",
            "cus_country": "Bangladesh",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(SESSION_URL, data=payload)
            res.raise_for_status()
            return res.json()

    async def validate_transaction(self, val_id: str) -> Dict[str, Any]:
        """Server-to-server check that a transaction SSLCommerz reports as paid is genuine.
        Never trust the success redirect alone — it can be forged by anyone who knows the URL."""
        params = {
            "val_id": val_id,
            "store_id": config.SSLCOMMERZ_STORE_ID,
            "store_passwd": config.SSLCOMMERZ_STORE_PASSWORD,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(VALIDATION_URL, params=params)
            res.raise_for_status()
            return res.json()


sslcommerz_service = SSLCommerzService()
