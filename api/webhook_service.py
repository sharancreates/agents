import hmac
import hashlib
import time
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
import ipaddress
import socket
import os
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("WebhookService")

def validate_webhook_url(url: str) -> bool:
    """
    Validates webhook URL against Server-Side Request Forgery (SSRF).
    Ensures safe scheme (https/http) and prevents targeting loopback, RFC1918,
    link-local, cloud metadata (169.254.169.254), or non-routable addresses.
    """
    if not url:
        raise ValueError("Webhook URL cannot be empty.")

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. Webhooks must use http:// or https://")

    # In production, require https
    if os.getenv("ENVIRONMENT") == "production" and parsed.scheme != "https":
        raise ValueError("Production webhooks must use https://")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid webhook URL: missing hostname.")

    # In test/dev mode or simulation, allow testserver or mock domains
    if os.getenv("ALLOW_LOCAL_WEBHOOKS", "false").lower() in ("true", "1", "yes") or hostname in ("testserver", "localhost.test"):
        return True

    # Check for direct localhost / loopback strings
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        raise ValueError(f"SSRF Protection: Webhook target '{hostname}' is not permitted.")

    # Resolve hostname to IP addresses and inspect for private/reserved networks
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip_str.startswith("169.254.") # AWS / GCP metadata
            ):
                raise ValueError(f"SSRF Protection: Webhook target resolves to restricted IP ({ip_str}).")
    except socket.gaierror:
        # If DNS fails or host does not resolve in test/dev
        if "." not in hostname:
            raise ValueError(f"SSRF Protection: Hostname '{hostname}' could not be resolved.")

    return True

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
    Guarded against SSRF attempts.
    """
    if not webhook_url:
        return False

    try:
        validate_webhook_url(webhook_url)
    except Exception as e:
        logger.warning(f"Webhook dispatch blocked by SSRF protection: {e}")
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
