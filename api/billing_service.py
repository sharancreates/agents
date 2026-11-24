import datetime
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from api import models
from api.razorpay_client import (
    get_razorpay_client,
    verify_payment_signature,
    verify_webhook_signature,
    RAZORPAY_KEY_ID
)

logger = logging.getLogger("BillingService")

# Commercial Credit Packages
CREDIT_PACKAGES: Dict[str, Dict[str, Any]] = {
    "starter_100": {
        "id": "starter_100",
        "name": "Team / Bootcamp Pack",
        "credits": 100,
        "amount_paise": 49900,  # ₹499
        "currency": "INR",
        "description": "100 autonomous evaluation credits (₹4.99/eval)"
    },
    "pro_500": {
        "id": "pro_500",
        "name": "Organizer Pro Pack",
        "credits": 500,
        "amount_paise": 199900,  # ₹1,999
        "currency": "INR",
        "description": "500 autonomous evaluation credits (₹3.99/eval)"
    },
    "enterprise_2000": {
        "id": "enterprise_2000",
        "name": "Enterprise Hackathon Pass",
        "credits": 2000,
        "amount_paise": 599900,  # ₹5,999
        "currency": "INR",
        "description": "2,000 autonomous evaluation credits (₹2.99/eval)"
    }
}

class BillingService:
    @staticmethod
    def get_or_create_credit_account(db: Session, org_id: int) -> models.OrganizationCredit:
        """
        Retrieves the organization's credit record or provisions an initial
        starter account with 25 free evaluation credits.
        """
        credit = db.query(models.OrganizationCredit).filter(
            models.OrganizationCredit.organization_id == org_id
        ).first()

        if not credit:
            credit = models.OrganizationCredit(
                organization_id=org_id,
                balance=25.0,  # Default free tier starter allocation
                total_purchased=0.0,
                total_consumed=0.0
            )
            db.add(credit)
            db.commit()
            db.refresh(credit)
            logger.info(f"Provisioned initial credit account for Org #{org_id} with 25 credits.")

        return credit

    @staticmethod
    def get_balance(db: Session, org_id: int) -> Dict[str, Any]:
        """Returns credit balance and summary for an organization."""
        account = BillingService.get_or_create_credit_account(db, org_id)
        org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
        tier = org.tier if org else "free"
        return {
            "organization_id": org_id,
            "tier": tier,
            "balance": account.balance,
            "total_purchased": account.total_purchased,
            "total_consumed": account.total_consumed,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
            "packages_available": list(CREDIT_PACKAGES.values())
        }

    @staticmethod
    def create_order(db: Session, org_id: int, package_id: str) -> Dict[str, Any]:
        """
        Initiates a checkout order with Razorpay in integer paise.
        Persists order in database with status='created'.
        """
        if package_id not in CREDIT_PACKAGES:
            raise ValueError(f"Invalid package_id '{package_id}'. Supported packages: {list(CREDIT_PACKAGES.keys())}")

        pkg = CREDIT_PACKAGES[package_id]
        client = get_razorpay_client()
        
        timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        receipt = f"rcpt_org{org_id}_{timestamp}"

        order_data = {
            "amount": pkg["amount_paise"],
            "currency": pkg["currency"],
            "receipt": receipt,
            "notes": {
                "organization_id": str(org_id),
                "package_id": package_id,
                "credits": str(pkg["credits"])
            }
        }

        try:
            rzp_order = client.orders.create(data=order_data)
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            raise RuntimeError(f"Payment gateway error: {e}")

        # Persist order record in database
        order_record = models.PaymentOrder(
            organization_id=org_id,
            package_id=package_id,
            razorpay_order_id=rzp_order["id"],
            amount_paise=pkg["amount_paise"],
            currency=pkg["currency"],
            credits_to_grant=pkg["credits"],
            status="created"
        )
        db.add(order_record)
        db.commit()
        db.refresh(order_record)

        return {
            "order_id": rzp_order["id"],
            "amount_paise": pkg["amount_paise"],
            "amount_inr": pkg["amount_paise"] / 100.0,
            "currency": pkg["currency"],
            "credits_to_grant": pkg["credits"],
            "package_name": pkg["name"],
            "key_id": RAZORPAY_KEY_ID
        }

    @staticmethod
    def verify_and_credit_payment(
        db: Session,
        org_id: int,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> Dict[str, Any]:
        """
        Cryptographically verifies payment HMAC-SHA256 signature, prevents replay/double-spend,
        and atomically credits the organization's balance.
        """
        # 1. Cryptographic Signature Verification
        if not verify_payment_signature(order_id, payment_id, signature):
            logger.warning(f"Payment verification rejected: Invalid signature for Order {order_id}, Payment {payment_id}")
            raise ValueError("Invalid payment signature. Verification failed.")

        # 2. Double-Spend & Replay Check
        existing_paid = db.query(models.PaymentOrder).filter(
            models.PaymentOrder.razorpay_payment_id == payment_id,
            models.PaymentOrder.status == "paid"
        ).first()
        if existing_paid:
            logger.warning(f"Replay attack blocked: Payment ID {payment_id} was already credited.")
            raise ValueError("Payment ID has already been credited. Replay rejected.")

        # 3. Order lookup and validation
        order = db.query(models.PaymentOrder).filter(
            models.PaymentOrder.razorpay_order_id == order_id
        ).first()

        if not order:
            raise ValueError(f"Order ID '{order_id}' not found.")
        if order.organization_id != org_id:
            raise ValueError("Order does not belong to the calling organization.")
        if order.status == "paid":
            raise ValueError(f"Order '{order_id}' has already been fulfilled.")

        # 4. Atomic credit grant & order state transition
        account = BillingService.get_or_create_credit_account(db, org_id)
        
        order.razorpay_payment_id = payment_id
        order.status = "paid"
        order.paid_at = datetime.datetime.now(datetime.timezone.utc)

        account.balance += float(order.credits_to_grant)
        account.total_purchased += float(order.credits_to_grant)
        account.updated_at = datetime.datetime.now(datetime.timezone.utc)

        db.commit()
        db.refresh(account)
        db.refresh(order)

        logger.info(
            f"Successfully credited {order.credits_to_grant} credits to Org #{org_id} "
            f"for Payment {payment_id}. New balance: {account.balance}"
        )

        return {
            "status": "success",
            "message": f"Successfully credited {order.credits_to_grant} evaluation credits.",
            "order_id": order.razorpay_order_id,
            "payment_id": payment_id,
            "credits_granted": order.credits_to_grant,
            "new_balance": account.balance
        }

    @staticmethod
    def process_webhook_event(
        db: Session,
        raw_body: bytes,
        signature: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates incoming Razorpay webhook signature and processes payment events asynchronously.
        """
        if not verify_webhook_signature(raw_body, signature):
            raise ValueError("Invalid webhook signature.")

        event = payload.get("event")
        logger.info(f"Received verified Razorpay webhook event: {event}")

        if event in ("payment.captured", "order.paid"):
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")

            if order_id and payment_id:
                order = db.query(models.PaymentOrder).filter(
                    models.PaymentOrder.razorpay_order_id == order_id
                ).first()
                if order and order.status != "paid":
                    account = BillingService.get_or_create_credit_account(db, order.organization_id)
                    order.razorpay_payment_id = payment_id
                    order.status = "paid"
                    order.paid_at = datetime.datetime.now(datetime.timezone.utc)
                    account.balance += float(order.credits_to_grant)
                    account.total_purchased += float(order.credits_to_grant)
                    account.updated_at = datetime.datetime.now(datetime.timezone.utc)
                    db.commit()
                    return {"processed": True, "event": event, "order_id": order_id}

        return {"processed": True, "event": event, "status": "ignored"}

    @staticmethod
    def has_sufficient_credits(db: Session, org_id: int, required_credits: float = 1.0) -> bool:
        """Checks if organization has at least `required_credits` in its account."""
        account = BillingService.get_or_create_credit_account(db, org_id)
        return account.balance >= required_credits

    @staticmethod
    def deduct_credit(
        db: Session,
        org_id: int,
        submission_id: Optional[str] = None,
        credits: float = 1.0,
        reason: str = "submission_evaluation"
    ) -> bool:
        """
        Atomically decrements credit balance and records an immutable UsageEvent ledger entry.
        """
        account = BillingService.get_or_create_credit_account(db, org_id)
        if account.balance < credits:
            logger.warning(f"Credit deduction failed: Org #{org_id} balance {account.balance} < {credits}")
            return False

        account.balance = max(0.0, account.balance - credits)
        account.total_consumed += credits
        account.updated_at = datetime.datetime.now(datetime.timezone.utc)

        usage = models.UsageEvent(
            organization_id=org_id,
            submission_id=submission_id,
            credits_deducted=credits,
            balance_after=account.balance,
            reason=reason
        )
        db.add(usage)
        db.commit()

        logger.info(f"Deducted {credits} credits from Org #{org_id}. New balance: {account.balance}")
        return True

    @staticmethod
    def get_usage_history(db: Session, org_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves chronological audit trail of credit usage for an organization."""
        events = db.query(models.UsageEvent).filter(
            models.UsageEvent.organization_id == org_id
        ).order_by(models.UsageEvent.created_at.desc()).limit(limit).all()

        return [
            {
                "id": ev.id,
                "submission_id": ev.submission_id,
                "credits_deducted": ev.credits_deducted,
                "balance_after": ev.balance_after,
                "reason": ev.reason,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in events
        ]
