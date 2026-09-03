# AgentCheckout-Guard: Deterministic Safety Middleware for Agentic Commerce

[![Track](https://img.shields.io/badge/Razorpay_Track-01:_AI_Growth_%26_Agentic_Commerce-blue.svg)](https://razorpay.com)
[![Status](https://img.shields.io/badge/Status-Complete-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

An autonomous, tool-calling purchasing agent integrated with Razorpay's Test Sandbox, governed by a strict deterministic safety middleware layer (`SafetyGuard`).

It mitigates the fundamental vulnerabilities of AI-driven financial execution: price hallucinations, budget blowouts, race-condition double billing, and stockout attempts.

---

## 1. System Architecture

                                  [ User Intent ]
                                         │
                                         ▼
                     [ Autonomous Agent (Gemini API Flash) ]
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
            get_catalog() (Tool)                   execute_order() (Tool)
                     │                                       │
            [ catalog.json (Truth) ]                         ▼
                                                   [ SafetyGuard Gating ]
                                                             │
                  ┌──────────────────────────────────────────┴──────────────────────────┐
                  ▼                                                                     ▼
        [ REJECTED: Gate Failed ]                                             [ APPROVED: All Clear ]
                  │                                                                     │
                  ├─► Anti-Hallucination Check (Price Drift)                            ├─► Append to audit_trail.jsonl
                  ├─► Idempotency Guard (Duplicate Receipt)                             └─► Razorpay Order Creation API
                  ├─► Stock/Inventory Availability                                               │
                  ├─► Financial Budget Boundary (Max ₹2,000)                                     ▼
                  │                                                                     [ order_id Output ]
                  ▼
        [ audit_trail.jsonl (Immutable Audit) ]

---

## 2. Core Guardrails Enforced

| Gate | Vulnerability Addressed | Implementation Detail |
| :--- | :--- | :--- |
| **Price Consistency** | LLM hallucinations or prompt injection attacks claiming lower prices. | Rejects transactions where `claimed_unit_price != catalog.price_paise`. |
| **Inventory State** | Ordering unavailable or out-of-stock items. | Deterministic check against current stock counts prior to payment order creation. |
| **Financial Bounding** | Runaway spending loops or unauthorized large expenditures. | Hard session cap (₹2,000 / 200,000 paise) intercepting requests before reaching payment APIs. |
| **Idempotency** | Network retries or agent self-loops creating duplicate charges. | Deduplication registry rejecting previously executed receipt IDs. |
| **Immutable Audit** | Lack of forensic traceability in autonomous agent flows. | Append-only event streaming logged to `audit_trail.jsonl` with reasons and timestamps. |

---

## 3. Project Structure

agentic-commerce-guard/
│
├── catalog.json          # Ground-truth product catalog (pricing in paise & inventory)
├── payment_service.py    # Thin wrapper for Razorpay Test Sandbox API
├── guardrails.py         # Deterministic SafetyGuard middleware and audit logger
├── agent.py              # Autonomous Gemini function-calling agent
├── test_breakage.py      # Edge-case verification suite ("2 AM failure test")
├── requirements.txt      # Dependency specification
├── audit_trail.jsonl     # Append-only execution record
└── README.md             # Architecture and submission documentation

## 4. Setup and Local Execution
Prerequisites:

1. Python 3.10+
2. Active Razorpay Test Sandbox Keys
3. Google Gemini API Key
   

Installation
Clone the repository:

git clone-  https://github.com/Annyatoma/agentic-commerce-guard.git

cd agentic-commerce-guard

Create and activate virtual environment:

python -m venv venv

Windows PowerShell:  .\venv\Scripts\Activate.ps1

macOS/Linux:  source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Configure Environment Variables:

Create a .env file in the root directory:

RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
GEMINI_API_KEY=your_gemini_api_key

## 5. Verification & Testing

1. Happy-Path Agent Execution
Runs the full autonomous purchase flow (Catalog Lookup → Price Resolution → Safety Gating → Live Razorpay Order Creation):
Bash
python agent.py
2. Edge-Case / Failure Simulation Suite
   
Tests the 4 critical failure modes deterministically:

python test_breakage.py

Expected Output:

Test 1 (Hallucination): Blocked due to claimed price mismatch.

Test 2 (Out of Stock): Blocked due to 0 inventory.

Test 3 (Budget Cap): Blocked because amount exceeds ₹2,000 threshold.

Test 4 (Idempotency): First attempt approved; replay blocked.

## 6. ProductionRoadmap

Distributed State: Replace local in-memory receipt deduplication with Redis TTL-based distributed locks.

Live Catalog Integration: Bind product validation directly to Razorpay's Item Catalog API.

Webhook Finalization: Consume Razorpay payment authorized/captured webhooks to update inventory asynchronously.
