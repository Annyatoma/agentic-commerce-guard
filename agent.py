import os
import json
import time
import uuid
import pathlib
from google import genai
from google.genai import types
from dotenv import load_dotenv
from guardrails import SafetyGuard
from payment_service import RazorpayService

env_path = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
guard = SafetyGuard()
payment_service = RazorpayService()

def get_catalog() -> str:
    """Returns all available products from the store catalog."""
    with open("catalog.json", "r") as f:
        return f.read()

def execute_order(product_id: str, quantity: int, claimed_unit_price: int) -> str:
    """Executes a payment order on Razorpay with deterministic safety gates."""
    receipt_id = f"rcpt_{uuid.uuid4().hex[:8]}"
    passed, reason, amount = guard.validate_and_gate_order(
        product_id=product_id,
        quantity=quantity,
        claimed_unit_price=claimed_unit_price,
        receipt_id=receipt_id
    )

    if passed:
        rzp_order = payment_service.create_order(
            amount_paise=amount,
            receipt_id=receipt_id,
            notes={"product_id": product_id, "source": "agentic_checkout"}
        )
        return json.dumps({
            "status": "SUCCESS",
            "razorpay_order_id": rzp_order["id"],
            "amount_paid_inr": amount / 100,
            "message": "Transaction verified and order created."
        })
    else:
        return json.dumps({
            "status": "BLOCKED",
            "reason": reason
        })

def run_agent(user_query: str):
    print(f"\n==========================================")
    print(f"USER PROMPT: {user_query}")
    print(f"==========================================")

    # Use the official required model
    model_name = "gemini-3.6-flash"

    chat = client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an autonomous e-commerce purchasing agent. "
                "Always check the catalog using get_catalog before placing an order to verify product ID, availability, and the exact price in paise. "
                "Never invent or guess prices. After checking, call execute_order to finish the transaction."
            ),
            tools=[get_catalog, execute_order]
        )
    )

    # Retry loop to gracefully handle temporary 503 spikes
    for attempt in range(4):
        try:
            response = chat.send_message(user_query)
            print(f"\nAGENT RESPONSE:\n{response.text}\n")
            return response.text
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"[Notice] Upstream load spike (503). Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
            else:
                raise e

if __name__ == "__main__":
    # Happy Path Test: Wireless Mouse is Rs. 1200 (within Rs. 2000 cap)
    run_agent("Please order 1 Wireless Mouse for me.")