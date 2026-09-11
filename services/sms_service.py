import logging
import httpx
from typing import Dict, Any
import config

logger = logging.getLogger("shohay.sms")

class SMSService:
    """
    Twilio SMS dispatch service with local mock fallback.
    Sends one-time security codes (OTP) to user mobile numbers.
    """

    def __init__(self):
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.from_phone = config.TWILIO_PHONE_NUMBER

    def format_phone_number(self, phone: str) -> str:
        """
        Normalizes Bangladeshi local numbers (e.g. 01712345678) to E.164 (+8801712345678)
        while preserving already formatted numbers.
        """
        p = phone.strip().replace(" ", "").replace("-", "")
        if p.startswith("+"):
            return p
        if p.startswith("880"):
            return f"+{p}"
        if p.startswith("01"):
            return f"+880{p[1:]}"
        return p

    def send_otp_sms(self, to_phone: str, otp: str) -> Dict[str, Any]:
        """
        Sends an SMS OTP. If Twilio keys are configured, invokes Twilio API.
        Otherwise, falls back to logging mock OTP for local development.
        """
        formatted_phone = self.format_phone_number(to_phone)
        message_body = (
            f"[Shohay - সহায়] Your emergency login verification code is {otp}. "
            f"Valid for {config.OTP_EXPIRATION_SECONDS // 60} minutes. Do not share this code with anyone."
        )

        if not config.TWILIO_CONFIGURED:
            # Fallback: log to server stdout for developers
            print(f"\n📱 [TWILIO DEV MOCK] SMS to {formatted_phone}:")
            print(f"   Message: \"{message_body}\"")
            print(f"   -> OTP: {otp}\n")
            logger.info(f"[TWILIO MOCK] Dispatched simulated SMS to {formatted_phone} (OTP: {otp})")
            return {
                "success": True,
                "provider": "mock",
                "phone": formatted_phone,
                "message": "SMS simulated in development mode. Check console/debug_otp."
            }

        # Real Twilio REST API request via httpx
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        auth = (self.account_sid, self.auth_token)
        data = {
            "From": self.from_phone,
            "To": formatted_phone,
            "Body": message_body
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, auth=auth, data=data)
                if response.status_code in (200, 201):
                    res_json = response.json()
                    logger.info(f"[TWILIO] SMS successfully sent to {formatted_phone} (SID: {res_json.get('sid')})")
                    return {
                        "success": True,
                        "provider": "twilio",
                        "sid": res_json.get("sid"),
                        "phone": formatted_phone,
                        "message": "SMS dispatched via Twilio."
                    }
                else:
                    err_msg = f"Twilio API Error {response.status_code}: {response.text}"
                    logger.error(err_msg)
                    return {
                        "success": False,
                        "provider": "twilio",
                        "error": err_msg,
                        "message": "Failed to send SMS via Twilio."
                    }
        except Exception as exc:
            err_msg = f"Failed connecting to Twilio: {str(exc)}"
            logger.error(err_msg)
            return {
                "success": False,
                "provider": "twilio",
                "error": err_msg,
                "message": "Twilio connection error."
            }


sms_service = SMSService()
