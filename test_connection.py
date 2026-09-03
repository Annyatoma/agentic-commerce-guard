import os
import pathlib
import razorpay
from google import genai
from dotenv import load_dotenv

# Explicitly load .env from current script directory
env_path = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")
gemini_key = os.getenv("GEMINI_API_KEY")

print("1. Checking environment variables...")
if not key_id:
    print("❌ RAZORPAY_KEY_ID missing from .env")
if not key_secret:
    print("❌ RAZORPAY_KEY_SECRET missing from .env")
if not gemini_key:
    print("❌ GEMINI_API_KEY missing from .env (Did you press Ctrl+S?)")
    exit(1)

print(f"✅ Loaded Razorpay ID: {key_id[:12]}...")
print(f"✅ Loaded Gemini Key: {gemini_key[:8]}...")

print("\n2. Testing Razorpay...")
try:
    client = razorpay.Client(auth=(key_id, key_secret))
    order = client.order.create({
        "amount": 10000,
        "currency": "INR",
        "receipt": "sanity_check_02"
    })
    print(f"✅ Razorpay Success! Order ID: {order['id']}")
except Exception as e:
    print(f"❌ Razorpay Error: {e}")

print("\n3. Testing Gemini API...")
try:
    ai_client = genai.Client(api_key=gemini_key)
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'System Ready' in two words."
    )
    print(f"✅ Gemini Success! Response: {response.text.strip()}")
except Exception as e:
    print(f"❌ Gemini Error: {e}")

print("\nEnvironment setup complete.")