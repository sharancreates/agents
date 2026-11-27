import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api import models
from api.auth import get_current_org, get_db, require_scope
from api.billing_service import BillingService, CREDIT_PACKAGES

router = APIRouter(prefix="/v1/billing", tags=["Monetization & Razorpay Billing"])

# --- Request / Response Schemas ---

class CreateOrderRequest(BaseModel):
    package_id: str = Field(..., description="ID of credit package: starter_100, pro_500, or enterprise_2000")

class VerifyPaymentRequest(BaseModel):
    order_id: str = Field(..., description="Razorpay order ID (e.g. order_xxx)")
    payment_id: str = Field(..., description="Razorpay payment ID (e.g. pay_xxx)")
    signature: str = Field(..., description="HMAC-SHA256 signature returned by Razorpay Checkout")

# --- Endpoints ---

@router.get("/balance")
def get_credit_balance(
    auth_ctx: tuple = Depends(require_scope("billing:read")),
    db: Session = Depends(get_db)
):
    """
    Returns current organization credit balance, usage summary, and available top-up packages.
    """
    org, _ = auth_ctx
    return BillingService.get_balance(db, org.id)

@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_billing_order(
    request: CreateOrderRequest,
    auth_ctx: tuple = Depends(require_scope("billing:write")),
    db: Session = Depends(get_db)
):
    """
    Initiates a new Razorpay checkout order for the chosen credit package.
    Returns the order ID and key ID for client-side Razorpay Checkout modal.
    """
    org, _ = auth_ctx
    try:
        order = BillingService.create_order(db, org.id, request.package_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate checkout order: {str(e)}")

@router.post("/verify-payment")
def verify_payment(
    request: VerifyPaymentRequest,
    auth_ctx: tuple = Depends(require_scope("billing:write")),
    db: Session = Depends(get_db)
):
    """
    Verifies the cryptographic HMAC-SHA256 payment signature from Razorpay.
    Upon successful verification, atomically credits the organization's balance.
    Rejects double-spend attempts and tampered signatures.
    """
    org, _ = auth_ctx
    try:
        result = BillingService.verify_and_credit_payment(
            db=db,
            org_id=org.id,
            order_id=request.order_id,
            payment_id=request.payment_id,
            signature=request.signature
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment fulfillment failed: {str(e)}")

@router.post("/razorpay-webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db)
):
    """
    Asynchronous webhook endpoint for Razorpay payment captured events.
    Verifies X-Razorpay-Signature header against the raw request payload.
    """
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Missing X-Razorpay-Signature header"
        )

    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    try:
        result = BillingService.process_webhook_event(
            db=db,
            raw_body=raw_body,
            signature=x_razorpay_signature,
            payload=payload
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/usage")
def get_usage_ledger(
    limit: int = 50,
    auth_ctx: tuple = Depends(require_scope("billing:read")),
    db: Session = Depends(get_db)
):
    """
    Returns the immutable audit ledger of credit consumption for this organization.
    """
    org, _ = auth_ctx
    return BillingService.get_usage_history(db, org.id, limit=limit)
