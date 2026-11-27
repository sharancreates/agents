import os
import hmac
import hashlib
import time
import uuid
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("RazorpayClient")

DEFAULT_SIMULATED_KEY_SECRET = "simulated_secret_key_12345"
DEFAULT_SIMULATED_WEBHOOK_SECRET = "simulated_webhook_secret_67890"

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_simulated_key")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", DEFAULT_SIMULATED_KEY_SECRET)
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", DEFAULT_SIMULATED_WEBHOOK_SECRET)

def is_simulation_mode() -> bool:
    """
    Returns True only when explicitly running in test/simulation mode.
    In production deployments (ENVIRONMENT=production), simulation is strictly prohibited
    and missing credentials fail closed.
    """
    is_prod = (os.getenv("ENVIRONMENT", "development") == "production")
    if is_prod:
        return False

    key_id = os.getenv("RAZORPAY_KEY_ID")
    if key_id and key_id.startswith("rzp_live_"):
        return False

    # In non-production, allow explicit opt-in or test keys
    if os.getenv("RAZORPAY_SIMULATION", "false").lower() in ("true", "1", "yes"):
        return True
    if key_id and key_id.startswith("rzp_test_simulated"):
        return True
    if not key_id and (os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ENVIRONMENT", "development") in ("development", "test")):
        return True

    return False

def _resolve_secret(explicit_secret: Optional[str], env_var_name: str, simulated_default: str) -> str:
    """Resolves secret, prohibiting default simulated secrets in production mode."""
    secret = explicit_secret or os.getenv(env_var_name)
    if is_simulation_mode():
        return secret or simulated_default
    if not secret:
        raise ValueError(f"CRITICAL_SECURITY_ERROR: Production {env_var_name} must be set in environment.")
    if secret == simulated_default:
        raise ValueError(f"CRITICAL_SECURITY_ERROR: Default simulated secret for {env_var_name} is rejected in production mode.")
    return secret

def generate_payment_signature(order_id: str, payment_id: str, secret: Optional[str] = None) -> str:
    """
    Computes HMAC-SHA256 signature for Razorpay checkout verification.
    Formula: HMAC-SHA256(order_id + "|" + payment_id, secret)
    """
    key_secret = _resolve_secret(secret, "RAZORPAY_KEY_SECRET", DEFAULT_SIMULATED_KEY_SECRET)
    payload = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(key_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

def verify_payment_signature(
    order_id: str, 
    payment_id: str, 
    signature: str, 
    secret: Optional[str] = None
) -> bool:
    """
    Cryptographically verifies the payment signature submitted by client.
    Uses constant-time comparison to prevent timing side-channel attacks.
    """
    if not order_id or not payment_id or not signature:
        return False
    key_secret = _resolve_secret(secret, "RAZORPAY_KEY_SECRET", DEFAULT_SIMULATED_KEY_SECRET)
    expected_sig = generate_payment_signature(order_id, payment_id, key_secret)
    return hmac.compare_digest(expected_sig, signature)

def generate_webhook_signature(raw_body: bytes, secret: Optional[str] = None) -> str:
    """
    Computes HMAC-SHA256 signature for Razorpay webhook payloads.
    Formula: HMAC-SHA256(raw_body, webhook_secret)
    """
    key_secret = _resolve_secret(secret, "RAZORPAY_WEBHOOK_SECRET", DEFAULT_SIMULATED_WEBHOOK_SECRET)
    return hmac.new(key_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

def verify_webhook_signature(
    raw_body: bytes, 
    signature: str, 
    secret: Optional[str] = None
) -> bool:
    """
    Cryptographically validates Razorpay X-Razorpay-Signature on incoming webhooks.
    """
    if not raw_body or not signature:
        return False
    key_secret = _resolve_secret(secret, "RAZORPAY_WEBHOOK_SECRET", DEFAULT_SIMULATED_WEBHOOK_SECRET)
    expected_sig = generate_webhook_signature(raw_body, key_secret)
    return hmac.compare_digest(expected_sig, signature)

class SimulatedOrders:
    """Simulates the Razorpay .orders API collection for testing and offline environments."""
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        order_num = uuid.uuid4().hex[:14]
        order_id = f"order_{order_num}"
        amount = data.get("amount", 0)
        currency = data.get("currency", "INR")
        receipt = data.get("receipt", f"rcpt_{uuid.uuid4().hex[:8]}")
        notes = data.get("notes", {})
        
        logger.info(f"[SIMULATED RAZORPAY] Order created: {order_id} - {amount} {currency}")
        return {
            "id": order_id,
            "entity": "order",
            "amount": amount,
            "amount_paid": 0,
            "amount_due": amount,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "attempts": 0,
            "notes": notes,
            "created_at": int(time.time())
        }

class SimulatedRazorpayClient:
    """In-memory high-fidelity mock client for Razorpay."""
    def __init__(self, key_id: str = RAZORPAY_KEY_ID, key_secret: str = RAZORPAY_KEY_SECRET):
        self.key_id = key_id
        self.key_secret = key_secret
        self.orders = SimulatedOrders()

def get_razorpay_client():
    """
    Factory returning live Razorpay SDK Client if configured,
    or SimulatedRazorpayClient when explicitly in simulation mode.
    Fails closed if live credentials are configured but the SDK is missing.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    is_prod = (os.getenv("ENVIRONMENT", "development") == "production")

    if is_prod and (not key_id or not key_secret):
        raise RuntimeError("Payment gateway error: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured in production.")

    # If live/configured keys are present (or production mode)
    if (key_id and not key_id.startswith("rzp_test_simulated")) or is_prod:
        try:
            import razorpay
            return razorpay.Client(auth=(key_id, key_secret))
        except ImportError:
            raise RuntimeError(
                "CRITICAL_CONFIGURATION_ERROR: Live Razorpay credentials are configured, "
                "but the 'razorpay' Python SDK package is not installed."
            )

    if is_simulation_mode():
        return SimulatedRazorpayClient(key_id or RAZORPAY_KEY_ID, key_secret or RAZORPAY_KEY_SECRET)

    raise RuntimeError("Razorpay credentials are not configured and simulation mode is disabled.")
