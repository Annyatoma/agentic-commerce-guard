import json
import datetime
from typing import Tuple, Dict, Any

AUDIT_LOG_FILE = "audit_trail.jsonl"
SESSION_BUDGET_CAP_PAISE = 200000  # Rs. 2,000 threshold

class SafetyGuard:
    def __init__(self, catalog_path: str = "catalog.json"):
        with open(catalog_path, "r") as f:
            self.catalog = {item["id"]: item for item in json.load(f)}
        self.processed_receipts = set()

    def audit_log(self, status: str, action: str, details: Dict[str, Any], reason: str = ""):
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "action": action,
            "status": status,
            "reason": reason,
            "details": details
        }
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def validate_and_gate_order(self, product_id: str, quantity: int, claimed_unit_price: int, receipt_id: str) -> Tuple[bool, str, int]:
        # 1. Idempotency Check
        if receipt_id in self.processed_receipts:
            msg = f"Duplicate execution blocked: Receipt {receipt_id} was already processed."
            self.audit_log("BLOCKED", "CREATE_ORDER", {"receipt_id": receipt_id}, msg)
            return False, msg, 0

        # 2. Product Existence
        if product_id not in self.catalog:
            msg = f"Invalid item: Product {product_id} not found in catalog."
            self.audit_log("BLOCKED", "CREATE_ORDER", {"product_id": product_id}, msg)
            return False, msg, 0

        product = self.catalog[product_id]

        # 3. Stock Check
        if product["stock"] < quantity:
            msg = f"Inventory failure: Requested {quantity}, only {product['stock']} left for {product['name']}."
            self.audit_log("BLOCKED", "CREATE_ORDER", {"product_id": product_id, "stock": product["stock"]}, msg)
            return False, msg, 0

        # 4. Anti-Hallucination Price Check
        actual_price = product["price_paise"]
        if claimed_unit_price != actual_price:
            msg = f"Price drift/hallucination: Claimed Rs.{claimed_unit_price/100}, but catalog truth is Rs.{actual_price/100}."
            self.audit_log("BLOCKED", "CREATE_ORDER", {"claimed": claimed_unit_price, "truth": actual_price}, msg)
            return False, msg, 0

        # 5. Financial Bounding Gate
        total_amount = actual_price * quantity
        if total_amount > SESSION_BUDGET_CAP_PAISE:
            msg = f"Budget gate triggered: Total Rs.{total_amount/100} exceeds safety cap of Rs.{SESSION_BUDGET_CAP_PAISE/100}."
            self.audit_log("BLOCKED", "CREATE_ORDER", {"total": total_amount, "cap": SESSION_BUDGET_CAP_PAISE}, msg)
            return False, msg, 0

        self.processed_receipts.add(receipt_id)
        self.audit_log("APPROVED", "CREATE_ORDER", {"product_id": product_id, "total": total_amount}, "All gates passed.")
        return True, "Execution Approved", total_amount