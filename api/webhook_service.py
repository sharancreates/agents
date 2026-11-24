import hmac
import hashlib
import time
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("WebhookService")

def generate_webhook_signature(secret: str, payload_json: str, timestamp: int) -> str:
    """
    Computes a Stripe-style HMAC-SHA256 signature header:
    X-AutoJudge-Signature: t={timestamp},v1={signature}
    """
    to_sign = f"{timestamp}.{payload_json}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"

def verify_webhook_signature(
    secret: str,
    signature_header: str,
    payload_json: str,
    tolerance_seconds: int = 300
) -> bool:
    """
    Validates signature header and enforces timestamp freshness to prevent replay attacks.
    """
    if not signature_header or "t=" not in signature_header or "v1=" not in signature_header:
        return False

    try:
        parts = dict(item.split("=", 1) for item in signature_header.split(","))
        timestamp = int(parts.get("t", 0))
        received_sig = parts.get("v1", "")

        now = int(time.time())
        if abs(now - timestamp) > tolerance_seconds:
            logger.warning(f"Webhook signature rejected: timestamp {timestamp} outside tolerance {tolerance_seconds}s (now={now}).")
            return False

        to_sign = f"{timestamp}.{payload_json}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()

        return hmac.compare_digest(expected_sig, received_sig)
    except Exception as e:
        logger.warning(f"Webhook signature verification error: {e}")
        return False

def dispatch_webhook_event(
    webhook_url: str,
    secret: str,
    event_type: str,
    data: Dict[str, Any]
) -> bool:
    """
    Dispatches signed HMAC-SHA256 webhook notification to an external partner endpoint.
    """
    if not webhook_url:
        return False

    timestamp = int(time.time())
    payload = {
        "event": event_type,
        "timestamp": timestamp,
        "data": data
    }
    payload_json = json.dumps(payload, default=str)
    sig_header = generate_webhook_signature(secret, payload_json, timestamp)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "AutoJudge-Webhook/1.0",
        "X-AutoJudge-Signature": sig_header,
        "X-AutoJudge-Timestamp": str(timestamp)
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=payload_json.encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            success = (200 <= resp.status < 300)
            logger.info(f"Webhook dispatched to {webhook_url}: status={resp.status}")
            return success
    except Exception as e:
        logger.warning(f"Failed to deliver webhook to {webhook_url}: {e}")
        return False
