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
import secrets
import base64
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("WebhookService")

def get_webhook_encryption_key() -> bytes:
    """
    Resolves master encryption key for partner signing secrets.
    Fails closed in production if deployment does not configure a secret key.
    """
    master = os.getenv("WEBHOOK_ENCRYPTION_KEY") or os.getenv("APP_SECRET")
    if not master:
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError(
                "CRITICAL_SECURITY_ERROR: Production deployment must configure "
                "WEBHOOK_ENCRYPTION_KEY or APP_SECRET for webhook secret encryption."
            )
        # Development / CI test fallback
        master = "autojudge_default_master_enc_key_9988"
    return hashlib.sha256(master.encode("utf-8")).digest()

def encrypt_webhook_secret(plaintext: str) -> str:
    """Encrypts plaintext secret with HMAC-SHA256 CTR keystream using a random 16-byte nonce."""
    if not plaintext:
        return ""
    key = get_webhook_encryption_key()
    nonce = secrets.token_bytes(16)
    data = plaintext.encode("utf-8")

    keystream = bytearray()
    block_num = 0
    while len(keystream) < len(data):
        counter = block_num.to_bytes(4, "big")
        keystream.extend(hmac.new(key, nonce + counter, hashlib.sha256).digest())
        block_num += 1

    encrypted = bytes([b ^ k for b, k in zip(data, keystream[:len(data)])])
    token = nonce + encrypted
    return "enc_" + base64.urlsafe_b64encode(token).decode("ascii")

def decrypt_webhook_secret(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypts ciphertext created by encrypt_webhook_secret."""
    if not ciphertext:
        return None
    if not ciphertext.startswith("enc_"):
        return ciphertext

    try:
        raw = base64.urlsafe_b64decode(ciphertext[4:].encode("ascii"))
        if len(raw) < 16:
            return None
        nonce = raw[:16]
        encrypted = raw[16:]
        key = get_webhook_encryption_key()

        keystream = bytearray()
        block_num = 0
        while len(keystream) < len(encrypted):
            counter = block_num.to_bytes(4, "big")
            keystream.extend(hmac.new(key, nonce + counter, hashlib.sha256).digest())
            block_num += 1

        decrypted = bytes([b ^ k for b, k in zip(encrypted, keystream[:len(encrypted)])])
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to decrypt webhook secret: {e}")
        return None

def validate_webhook_url(url: str) -> bool:
    """
    Validates webhook URL against Server-Side Request Forgery (SSRF).
    Ensures safe scheme (https/http) and prevents targeting loopback, RFC1918,
    link-local, cloud metadata (169.254.169.254), or non-routable addresses.
    """
    is_valid, _ = resolve_and_validate_webhook_destination(url)
    return is_valid

def resolve_and_validate_webhook_destination(url: str) -> Tuple[bool, str]:
    """
    Validates webhook URL against SSRF and resolves its IP destination.
    Returns (is_valid, resolved_ip).
    Guards against both static private IP targets and dynamic DNS rebinding.
    """
    if not url:
        raise ValueError("Webhook URL cannot be empty.")

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. Webhooks must use http:// or https://")

    # In production, enforce HTTPS strictly
    is_prod = (os.getenv("ENVIRONMENT", "development") == "production")
    if is_prod and parsed.scheme != "https":
        raise ValueError("Production webhooks must use https://")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid webhook URL: missing hostname.")

    # In non-production testing, permit testserver, reserved documentation/test hostnames, or local webhooks
    if not is_prod and (
        os.getenv("ALLOW_LOCAL_WEBHOOKS", "false").lower() in ("true", "1", "yes")
        or hostname in ("testserver", "localhost.test", "mock-webhook.local")
        or hostname.endswith(".example.com")
        or hostname == "example.com"
        or hostname.endswith(".test")
    ):
        return True, "93.184.215.14" if "example.com" in hostname else "127.0.0.1"

    # Reject direct localhost / loopback strings
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        raise ValueError(f"SSRF Protection: Webhook target '{hostname}' is not permitted.")

    # Resolve hostname to IP addresses and inspect for private/reserved networks
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        if not addr_info:
            raise ValueError(f"SSRF Protection: Hostname '{hostname}' did not resolve to any addresses.")

        first_ip = addr_info[0][4][0]
        for _, _, _, _, sockaddr in addr_info:
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

        return True, first_ip
    except socket.gaierror:
        if "." not in hostname:
            raise ValueError(f"SSRF Protection: Hostname '{hostname}' could not be resolved.")
        raise ValueError(f"SSRF Protection: Hostname '{hostname}' could not be resolved via DNS.")

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
        _, validated_ip = resolve_and_validate_webhook_destination(webhook_url)
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

    parsed = urllib.parse.urlparse(webhook_url)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "AutoJudge-Webhook/1.0",
        "Host": parsed.netloc,
        "X-AutoJudge-Signature": sig_header,
        "X-AutoJudge-Timestamp": str(timestamp)
    }

    try:
        # If targeting local mock/testserver in test fixtures
        if parsed.hostname in ("testserver", "mock-webhook.local"):
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

        # Connect directly to the pre-validated IP to eliminate DNS rebinding race conditions
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        import http.client
        if parsed.scheme == "https":
            conn = http.client.HTTPSConnection(validated_ip, port=port, timeout=5.0)
        else:
            conn = http.client.HTTPConnection(validated_ip, port=port, timeout=5.0)

        conn.request("POST", path, body=payload_json.encode("utf-8"), headers=headers)
        resp = conn.getresponse()
        success = (200 <= resp.status < 300)
        conn.close()
        logger.info(f"Webhook dispatched to {webhook_url} via {validated_ip}: status={resp.status}")
        return success
    except Exception as e:
        logger.warning(f"Failed to deliver webhook to {webhook_url}: {e}")
        return False
