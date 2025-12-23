"""
Payment API Routes
Paystack checkout and webhook handling
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.payment_service import payment_service
from services.auth_service import auth_service, User
from api.auth_routes import get_current_user, require_auth
from config import PAYSTACK_PUBLIC_KEY, PRICE_MONTHLY_USD, GRANDFATHER_PRICE_USD, FUTURE_PRICE_USD


router = APIRouter(prefix="/payments", tags=["Payments"])


# ==================
# Request/Response Models
# ==================

class CreateCheckoutRequest(BaseModel):
    """Request to create checkout session"""
    email: EmailStr
    callback_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Response with checkout URL"""
    success: bool
    authorization_url: Optional[str] = None
    reference: Optional[str] = None
    message: Optional[str] = None


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response"""
    is_pro: bool
    subscription_status: Optional[str] = None
    current_period_end: Optional[str] = None
    price: int = PRICE_MONTHLY_USD
    grandfathered: bool = True


class PricingResponse(BaseModel):
    """Pricing information"""
    current_price: int
    future_price: int
    currency: str = "USD"
    is_grandfathered: bool = True
    paystack_public_key: str


# ==================
# Endpoints
# ==================

@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """
    Get current pricing information.
    Used by frontend to display pricing.
    """
    return PricingResponse(
        current_price=GRANDFATHER_PRICE_USD,
        future_price=FUTURE_PRICE_USD,
        currency="USD",
        is_grandfathered=True,
        paystack_public_key=PAYSTACK_PUBLIC_KEY
    )


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(request: CreateCheckoutRequest):
    """
    Create a Paystack checkout session.
    Returns URL to redirect user to for payment.
    """
    result = await payment_service.create_checkout_url(
        email=request.email,
        callback_url=request.callback_url
    )
    
    if result:
        return CheckoutResponse(
            success=True,
            authorization_url=result["authorization_url"],
            reference=result["reference"]
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to create checkout session. Please try again."
        )


@router.get("/verify/{reference}")
async def verify_payment(reference: str):
    """
    Verify a payment by reference.
    Called after user returns from Paystack.
    """
    result = await payment_service.verify_transaction(reference)
    
    if result:
        # Get or create user and update pro status
        email = result.get("customer", {}).get("email")
        if email:
            user = auth_service.get_or_create_user(email)
            auth_service.update_user_pro_status(
                email, 
                True,
                result.get("customer", {}).get("customer_code")
            )
            
            # Generate access token for auto-login
            if user:
                # Refresh user to get updated pro status
                user = auth_service.get_user_by_email(email)
                access_token = auth_service.create_access_token(user)
                
                return {
                    "success": True,
                    "user": user.model_dump(),
                    "access_token": access_token,
                    "message": "Payment successful! Welcome to Pro."
                }
        
        return {
            "success": True,
            "message": "Payment verified successfully"
        }
    else:
        return {
            "success": False,
            "message": "Payment not found or not completed"
        }


@router.post("/webhook")
async def paystack_webhook(request: Request):
    """
    Handle Paystack webhook events.
    Called by Paystack when payment events occur.
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    
    # Verify signature
    if not payment_service.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event
    try:
        event = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle the event
    success = await payment_service.handle_webhook(event)
    
    if success:
        return {"status": "success"}
    else:
        return {"status": "error"}


@router.get("/subscription-status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(user: User = Depends(require_auth)):
    """
    Get current user's subscription status.
    """
    status = await payment_service.get_subscription_status(user.email)
    
    subscription = status.get("subscription", {}) if status else {}
    
    return SubscriptionStatusResponse(
        is_pro=user.is_pro,
        subscription_status=subscription.get("status"),
        current_period_end=subscription.get("current_period_end"),
        price=GRANDFATHER_PRICE_USD,
        grandfathered=True
    )


@router.post("/cancel-subscription")
async def cancel_subscription(user: User = Depends(require_auth)):
    """
    Cancel the user's subscription.
    """
    if not user.is_pro:
        raise HTTPException(status_code=400, detail="No active subscription")
    
    # Get user's subscription code
    status = await payment_service.get_subscription_status(user.email)
    subscription_code = status.get("paystack_subscription_code") if status else None
    
    if not subscription_code:
        raise HTTPException(status_code=400, detail="Subscription not found")
    
    success = await payment_service.cancel_subscription(subscription_code)
    
    if success:
        return {"success": True, "message": "Subscription cancelled"}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")
