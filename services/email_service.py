import os
import logging
import httpx
from typing import Dict, Any
import config

logger = logging.getLogger("shohay.email")

class EmailService:
    """
    Resend Email dispatch service with local mock fallback.
    Sends one-time security codes (OTP) to user email addresses with responsive HTML styling.
    """

    @property
    def api_key(self) -> str:
        return os.getenv("RESEND_API_KEY", config.RESEND_API_KEY).strip()

    @property
    def from_email(self) -> str:
        return os.getenv("RESEND_FROM_EMAIL", config.RESEND_FROM_EMAIL).strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


    def _render_otp_html(self, otp: str) -> str:
        minutes = config.OTP_EXPIRATION_SECONDS // 60
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Shohay Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e5e7eb; overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="background-color: #0f172a; padding: 24px 32px; text-align: left;">
              <h2 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
                🌊 Shohay (সহায়)
              </h2>
              <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px;">Flood Relief & Disaster Response Coordination</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding: 32px; color: #334155;">
              <h3 style="margin: 0 0 12px 0; font-size: 18px; color: #0f172a;">Your Verification Code</h3>
              <p style="margin: 0 0 24px 0; font-size: 14px; line-height: 1.5; color: #475569;">
                Use the following 6-digit code to sign in or complete your registration on the Shohay platform.
              </p>
              <!-- Code Box -->
              <div style="background-color: #f1f5f9; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 24px; border: 1px dashed #cbd5e1;">
                <span style="font-family: 'SF Mono', Monaco, Consolas, monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #0284c7;">
                  {otp}
                </span>
              </div>
              <p style="margin: 0 0 8px 0; font-size: 13px; color: #64748b;">
                ⏰ This code will expire in <strong>{minutes} minutes</strong>.
              </p>
              <p style="margin: 0; font-size: 13px; color: #ef4444;">
                🔒 If you did not request this login code, please ignore this email.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; padding: 16px 32px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center;">
              Shohay National Disaster Response Network • Bangladesh
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    def send_otp_email(self, to_email: str, otp: str) -> Dict[str, Any]:
        """
        Sends an email OTP. If Resend API key is set, dispatches via Resend REST API.
        Otherwise, falls back to local console mock logging.
        """
        clean_email = to_email.strip().lower()

        if not self.is_configured:
            print(f"\n📧 [RESEND DEV MOCK] Email to {clean_email}:")
            print(f"   Subject: \"[Shohay] Your Login Code: {otp}\"")
            print(f"   -> OTP: {otp}\n")
            logger.info(f"[RESEND MOCK] Dispatched simulated Email to {clean_email} (OTP: {otp})")
            return {
                "success": True,
                "provider": "mock",
                "email": clean_email,
                "message": "Email simulated in development mode. Check console/debug_otp."
            }

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": self.from_email,
            "to": [clean_email],
            "subject": f"[Shohay] Your Login Code: {otp}",
            "html": self._render_otp_html(otp)
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 201):
                    res_json = response.json()
                    logger.info(f"[RESEND] Email sent to {clean_email} (ID: {res_json.get('id')})")
                    return {
                        "success": True,
                        "provider": "resend",
                        "id": res_json.get("id"),
                        "email": clean_email,
                        "message": "Email dispatched via Resend."
                    }
                else:
                    err_msg = f"Resend API Error {response.status_code}: {response.text}"
                    logger.error(err_msg)
                    # Friendly developer console log for Resend Sandbox restrictions
                    print(f"\n⚠️ [RESEND SANDBOX NOTICE] Could not send live email to '{clean_email}'.")
                    print(f"   Reason: Resend sandbox without custom domain only delivers to your registered account email.")
                    print(f"   🔑 [DEV OTP]: {otp} (Use this OTP to complete sign-in/registration in development!)\n")
                    return {
                        "success": False,
                        "provider": "resend",
                        "error": err_msg,
                        "fallback_otp": otp,
                        "message": f"Resend sandbox notice: Use test OTP '{otp}' in development."
                    }
        except Exception as exc:
            err_msg = f"Failed connecting to Resend: {str(exc)}"
            logger.error(err_msg)
            print(f"\n⚠️ [RESEND CONNECTION ERROR]: {err_msg}")
            print(f"   🔑 [DEV OTP]: {otp}\n")
            return {
                "success": False,
                "provider": "resend",
                "error": err_msg,
                "fallback_otp": otp,
                "message": "Resend connection error."
            }



email_service = EmailService()
