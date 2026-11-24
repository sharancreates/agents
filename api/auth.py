import hmac
import hashlib
import secrets
import datetime
import time
import collections
from typing import Optional, Tuple, List, Dict
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api import models

# In-memory sliding window rate limiter
_RATE_LIMIT_WINDOWS: Dict[int, collections.deque] = collections.defaultdict(collections.deque)

TIER_LIMITS = {
    "free": 10,        # 10 requests per minute
    "pro": 60,         # 60 requests per minute
    "enterprise": 300  # 300 requests per minute
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_secret(raw_secret: str) -> str:
    """Computes SHA-256 hexadecimal digest of raw secret."""
    return hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

def generate_api_key(
    db: Session,
    organization_id: int,
    name: str = "Default API Key",
    scopes: Optional[List[str]] = None
) -> Tuple[str, models.ApiKey]:
    """
    Generates a high-entropy Stripe-patterned API key: ak_live_{prefix}_{secret}.
    Returns (plaintext_key, api_key_db_record).
    The plaintext_key is only available at generation time and must be shown to the user once.
    """
    prefix = f"ak_live_{secrets.token_hex(4)}"
    secret = secrets.token_urlsafe(32)
    plaintext_key = f"{prefix}_{secret}"
    key_hash = hash_secret(plaintext_key)

    api_key_record = models.ApiKey(
        organization_id=organization_id,
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes or ["eval:read", "eval:write"],
        is_active=True
    )
    db.add(api_key_record)
    db.commit()
    db.refresh(api_key_record)

    return plaintext_key, api_key_record

def verify_api_key(db: Session, plaintext_key: str) -> Optional[Tuple[models.ApiKey, models.Organization]]:
    """
    Validates an incoming API key using constant-time hash comparison.
    Updates last_used_at and returns (ApiKey, Organization) or None.
    """
    if not plaintext_key or not (plaintext_key.startswith("ak_live_") or plaintext_key.startswith("ak_test_")):
        return None

    computed_hash = hash_secret(plaintext_key)
    parts = plaintext_key.split("_")
    if len(parts) < 3:
        return None

    prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"

    key_record = db.query(models.ApiKey).filter(
        models.ApiKey.key_prefix == prefix,
        models.ApiKey.is_active == True
    ).first()

    if not key_record:
        return None

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(key_record.key_hash, computed_hash):
        return None

    # Update last used timestamp
    key_record.last_used_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()

    org = db.query(models.Organization).filter(models.Organization.id == key_record.organization_id).first()
    return key_record, org

def check_rate_limit(org_id: int, tier: str = "free") -> Tuple[bool, int, int]:
    """
    Sliding window rate limit check.
    Returns (is_limited, remaining_quota, reset_seconds).
    """
    limit = TIER_LIMITS.get(tier.lower(), 10)
    now = time.time()
    window = _RATE_LIMIT_WINDOWS[org_id]

    # Evict timestamps older than 60 seconds
    while window and window[0] < now - 60.0:
        window.popleft()

    if len(window) >= limit:
        reset_in = int(60.0 - (now - window[0]))
        return True, 0, max(1, reset_in)

    window.append(now)
    remaining = max(0, limit - len(window))
    return False, remaining, 60

def get_current_org(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Tuple[models.Organization, models.ApiKey]:
    """
    FastAPI security dependency validating Authorization header: Bearer <ak_live_...>
    Enforces API key authentication and rate limiting per organization tier.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected 'Bearer ak_live_...'",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    result = verify_api_key(db, token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    key_record, org = result
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Organization associated with API key not found."
        )

    # Rate limiting check
    is_limited, remaining, reset_seconds = check_rate_limit(org.id, org.tier)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for tier '{org.tier}'. Limit is {TIER_LIMITS.get(org.tier, 10)} req/min.",
            headers={
                "Retry-After": str(reset_seconds),
                "X-RateLimit-Limit": str(TIER_LIMITS.get(org.tier, 10)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds)
            }
        )

    return org, key_record
