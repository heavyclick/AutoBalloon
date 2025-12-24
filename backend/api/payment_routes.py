"""
Payment Routes - LemonSqueezy Integration
"""
from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import hmac
import hashlib
import os

router = APIRouter(prefix="/api/payments", tags=["payments"])

# LemonSqueezy Configuration
LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_VARIANT_ID = os.getenv("LEMONSQUEEZY_VARIANT_ID", "")  # Your $99/month variant
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
APP_URL = os.getenv("APP_URL", "https://autoballoon.space")


class PricingResponse(BaseModel):
    monthly_price: int
    currency: str
    features: list[str]


class CheckoutRequest(BaseModel):
    email: str


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """Get current pricing information"""
    return PricingResponse(
        monthly_price=99,
        currency="USD",
        features=[
            "Unlimited blueprint processing",
            "AS9102 Form 3 Excel exports",
            "Permanent cloud storage",
            "Priority processing",
            "Email support"
        ]
    )


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(request: CheckoutRequest):
    """Create a LemonSqueezy checkout session"""
    
    if not LEMONSQUEEZY_API_KEY or not LEMONSQUEEZY_STORE_ID:
        raise HTTPException(status_code=500, detail="Payment not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.lemonsqueezy.com/v1/checkouts",
                headers={
                    "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
                    "Content-Type": "application/vnd.api+json",
                    "Accept": "application/vnd.api+json"
                },
                json={
                    "data": {
                        "type": "checkouts",
                        "attributes": {
                            "checkout_data": {
                                "email": request.email,
                                "custom": {
                                    "user_email": request.email
                                }
                            },
                            "product_options": {
                                "redirect_url": f"{APP_URL}/success",
                            }
                        },
                        "relationships": {
                            "store": {
                                "data": {
                                    "type": "stores",
                                    "id": LEMONSQUEEZY_STORE_ID
                                }
                            },
                            "variant": {
                                "data": {
                                    "type": "variants",
                                    "id": LEMONSQUEEZY_VARIANT_ID
                                }
                            }
                        }
                    }
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                checkout_url = data["data"]["attributes"]["url"]
                return CheckoutResponse(checkout_url=checkout_url)
            else:
                print(f"LemonSqueezy error: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to create checkout")
                
    except Exception as e:
        print(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Payment service error")


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """Handle LemonSqueezy webhook events"""
    
    body = await request.body()
    
    # Verify webhook signature
    if LEMONSQUEEZY_WEBHOOK_SECRET and x_signature:
        expected_signature = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, x_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    event_name = payload.get("meta", {}).get("event_name")
    
    if event_name == "subscription_created":
        # New subscription
        custom_data = payload.get("meta", {}).get("custom_data", {})
        user_email = custom_data.get("user_email")
        
        if user_email:
            # TODO: Update user to Pro in Supabase
            print(f"New Pro subscription: {user_email}")
            # In production:
            # await supabase.table("users").update({"is_pro": True}).eq("email", user_email).execute()
    
    elif event_name == "subscription_cancelled":
        custom_data = payload.get("meta", {}).get("custom_data", {})
        user_email = custom_data.get("user_email")
        
        if user_email:
            print(f"Subscription cancelled: {user_email}")
            # In production:
            # await supabase.table("users").update({"is_pro": False}).eq("email", user_email).execute()
    
    return {"status": "received"}


@router.get("/verify/{order_id}")
async def verify_payment(order_id: str):
    """Verify a payment/subscription status"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.lemonsqueezy.com/v1/orders/{order_id}",
                headers={
                    "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
                    "Accept": "application/vnd.api+json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data["data"]["attributes"]["status"]
                return {
                    "success": status == "paid",
                    "status": status
                }
            else:
                return {"success": False, "status": "not_found"}
                
    except Exception as e:
        print(f"Verify error: {e}")
        return {"success": False, "status": "error"}
