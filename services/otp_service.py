import time
import secrets
import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any, Tuple
import config

class OTPService:
    def __init__(self):
        # identifier -> { "otp": "...", "expires_at": float, "attempts": int, "verified": bool }
        self._store: Dict[str, Dict[str, Any]] = {}

    def generate_otp(self, identifier: str, channel: str = "phone") -> str:
        """
        Generate a secure 6-digit numeric OTP and store with expiration timestamp.
        """
        clean_id = identifier.strip().lower()
        # Secure 6-digit OTP
        otp = f"{secrets.randbelow(900000) + 100000}"
        
        expires_at = time.time() + config.OTP_EXPIRATION_SECONDS
        self._store[clean_id] = {
            "otp": otp,
            "expires_at": expires_at,
            "attempts": 0,
            "channel": channel,
            "verified": False
        }
        return otp

    def verify_otp(self, identifier: str, input_otp: str) -> Tuple[bool, str]:
        """
        Validates OTP against stored value and expiration time.
        Returns (is_valid, message).
        """
        clean_id = identifier.strip().lower()
        entry = self._store.get(clean_id)

        # Allow universal test OTP in development/testing mode if explicitly used
        if input_otp.strip() == "123456" and config.ENVIRONMENT in ("development", "test"):
            if entry:
                entry["verified"] = True
            return True, "OTP verified successfully (Dev bypass)."

        if not entry:
            return False, "No OTP request found for this phone/email or it has expired."

        if time.time() > entry["expires_at"]:
            del self._store[clean_id]
            return False, "OTP has expired. Please request a new one."

        if entry["attempts"] >= 5:
            del self._store[clean_id]
            return False, "Too many failed attempts. Please request a new OTP."

        if entry["otp"] != input_otp.strip():
            entry["attempts"] += 1
            remaining = 5 - entry["attempts"]
            return False, f"Invalid OTP code. {remaining} attempt(s) remaining."

        # Mark verified
        entry["verified"] = True
        return True, "OTP verified successfully."

    def is_verified(self, identifier: str) -> bool:
        clean_id = identifier.strip().lower()
        entry = self._store.get(clean_id)
        if entry and entry.get("verified"):
            return True
        return False

    def clear_otp(self, identifier: str):
        clean_id = identifier.strip().lower()
        if clean_id in self._store:
            del self._store[clean_id]

    # ── Token Generation (HMAC-SHA256 Signed JSON Web Token) ──

    def create_token(self, payload: Dict[str, Any], expire_days: int = 30) -> str:
        """
        Creates a tamper-proof signed bearer token without external dependencies.
        """
        header = {"alg": "HS256", "typ": "JWT"}
        exp = int(time.time()) + (expire_days * 86400)
        full_payload = {**payload, "exp": exp, "iat": int(time.time())}

        def b64_encode(data: dict) -> str:
            raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
            return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

        encoded_header = b64_encode(header)
        encoded_payload = b64_encode(full_payload)
        signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")

        sig = hmac.new(
            config.JWT_SECRET.encode("utf-8"),
            signature_input,
            hashlib.sha256
        ).digest()
        encoded_sig = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")

        return f"{encoded_header}.{encoded_payload}.{encoded_sig}"

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes and verifies token signature and expiration.
        """
        try:
            parts = token.strip().split(".")
            if len(parts) != 3:
                return None
            encoded_header, encoded_payload, encoded_sig = parts

            # Verify signature
            signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
            expected_sig = hmac.new(
                config.JWT_SECRET.encode("utf-8"),
                signature_input,
                hashlib.sha256
            ).digest()
            expected_encoded_sig = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")

            if not hmac.compare_digest(encoded_sig, expected_encoded_sig):
                return None

            # Decode payload
            padded_payload = encoded_payload + "=" * (-len(encoded_payload) % 4)
            payload_raw = base64.urlsafe_b64decode(padded_payload).decode("utf-8")
            payload = json.loads(payload_raw)

            # Check expiration
            if payload.get("exp") and time.time() > payload["exp"]:
                return None

            return payload
        except Exception:
            return None


otp_service = OTPService()
