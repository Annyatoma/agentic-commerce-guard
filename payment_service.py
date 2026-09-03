import os
import pathlib
import uuid
import razorpay
from dotenv import load_dotenv

env_path = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class RazorpayService:
    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials missing from .env")
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount_paise: int, receipt_id: str = None, notes: dict = None):
        if not receipt_id:
            receipt_id = f"rcpt_{uuid.uuid4().hex[:8]}"

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt_id,
            "notes": notes or {}
        }
        order = self.client.order.create(data=payload)
        return order