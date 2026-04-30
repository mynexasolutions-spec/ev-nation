from __future__ import annotations

import hmac
import hashlib
import razorpay

from app.core.config import settings


class PaymentService:
    """Wrapper around the Razorpay Python SDK."""

    def __init__(self) -> None:
        self._client: razorpay.Client | None = None

    @property
    def client(self) -> razorpay.Client:
        if settings.razorpay_key_id == "rzp_test_change_me" or settings.razorpay_key_secret == "change_me":
            raise RuntimeError("Razorpay keys are not configured. Please add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to your .env file.")
            
        if self._client is None:
            self._client = razorpay.Client(
                auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            )
        return self._client

    def create_order(
        self, amount_paise: int, receipt: str, currency: str = "INR",
    ) -> dict:
        """Create a Razorpay order. Returns the full Razorpay response dict."""
        data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1,  # Auto-capture
        }
        return self.client.order.create(data=data)

    def verify_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify the Razorpay payment signature."""
        try:
            self.client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
