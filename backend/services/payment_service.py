"""
Payment Service
Handles Paystack integration for subscriptions
"""
import hmac
import hashlib
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from services.database_service import get_db
from services.auth_service import auth_service
from services.email_service import email_service
from config import (
    PAYSTACK_SECRET_KEY,
    PAYSTACK_PUBLIC_KEY,
    PAYSTACK_PLAN_CODE,
    PAYSTACK_WEBHOOK_SECRET,
    APP_URL,
    PRICE_MONTHLY_NGN,
)


class PaymentService:
    """
    Paystack payment service for subscription management.
    """
    
    PAYSTACK_API_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = PAYSTACK_SECRET_KEY
        self.public_key = PAYSTACK_PUBLIC_KEY
        self.plan_code = PAYSTACK_PLAN_CODE
        self.db = None
    
    def _get_db(self):
        """Lazy load database client"""
        if self.db is None:
            self.db = get_db()
        return self.db
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Paystack API headers"""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    # ==================
    # Checkout Methods
    # ==================
    
    async def create_checkout_url(self, email: str, callback_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Initialize a Paystack transaction for subscription.
        
        Args:
            email: Customer's email
            callback_url: URL to redirect after payment
            
        Returns:
            Dict with authorization_url and reference
        """
        if not callback_url:
            callback_url = f"{APP_URL}/success"
        
        payload = {
            "email": email,
            "amount": PRICE_MONTHLY_NGN * 100,  # Paystack uses kobo (cents)
            "currency": "NGN",
            "callback_url": callback_url,
            "plan": self.plan_code,  # For recurring subscription
            "metadata": {
                "product": "AutoBalloon Pro",
                "plan_type": "monthly"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.PAYSTACK_API_URL}/transaction/initialize",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status"):
                    return {
                        "authorization_url": data["data"]["authorization_url"],
                        "reference": data["data"]["reference"],
                        "access_code": data["data"]["access_code"]
                    }
                return None
                
        except Exception as e:
            print(f"Error creating checkout: {e}")
            return None
    
    async def verify_transaction(self, reference: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Paystack transaction.
        
        Args:
            reference: Transaction reference
            
        Returns:
            Transaction data if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.PAYSTACK_API_URL}/transaction/verify/{reference}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") and data["data"]["status"] == "success":
                    return data["data"]
                return None
                
        except Exception as e:
            print(f"Error verifying transaction: {e}")
            return None
    
    # ==================
    # Webhook Methods
    # ==================
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Paystack webhook signature.
        
        Args:
            payload: Raw request body
            signature: X-Paystack-Signature header
            
        Returns:
            True if valid
        """
        if not PAYSTACK_WEBHOOK_SECRET:
            # In development, skip verification
            return True
        
        computed = hmac.new(
            PAYSTACK_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed, signature)
    
    async def handle_webhook(self, event: Dict[str, Any]) -> bool:
        """
        Handle Paystack webhook events.
        
        Args:
            event: Webhook event data
            
        Returns:
            True if handled successfully
        """
        event_type = event.get("event")
        data = event.get("data", {})
        
        # Log the event
        await self._log_payment_event(event_type, data)
        
        # Handle specific events
        if event_type == "charge.success":
            return await self._handle_charge_success(data)
        
        elif event_type == "subscription.create":
            return await self._handle_subscription_created(data)
        
        elif event_type == "subscription.disable":
            return await self._handle_subscription_cancelled(data)
        
        elif event_type == "invoice.payment_failed":
            return await self._handle_payment_failed(data)
        
        return True
    
    async def _handle_charge_success(self, data: Dict[str, Any]) -> bool:
        """Handle successful charge"""
        email = data.get("customer", {}).get("email")
        customer_code = data.get("customer", {}).get("customer_code")
        
        if not email:
            return False
        
        # Get or create user
        user = auth_service.get_or_create_user(email)
        if not user:
            return False
        
        # Update to Pro status
        auth_service.update_user_pro_status(email, True, customer_code)
        
        # Send welcome email (only for first payment)
        if not user.is_pro:
            email_service.send_welcome_email(email)
        
        return True
    
    async def _handle_subscription_created(self, data: Dict[str, Any]) -> bool:
        """Handle new subscription"""
        email = data.get("customer", {}).get("email")
        subscription_code = data.get("subscription_code")
        plan_code = data.get("plan", {}).get("plan_code")
        
        if not email:
            return False
        
        try:
            db = self._get_db()
            
            # Get user
            user_result = db.table("users").select("id").eq(
                "email", email.lower()
            ).single().execute()
            
            if not user_result.data:
                return False
            
            user_id = user_result.data["id"]
            
            # Update user's subscription code
            db.table("users").update({
                "paystack_subscription_code": subscription_code,
                "is_pro": True
            }).eq("id", user_id).execute()
            
            # Create subscription record
            db.table("subscriptions").insert({
                "user_id": user_id,
                "paystack_subscription_code": subscription_code,
                "paystack_plan_code": plan_code,
                "status": "active",
                "amount": data.get("amount", PRICE_MONTHLY_NGN * 100),
                "currency": "NGN",
                "current_period_start": datetime.utcnow().isoformat()
            }).execute()
            
            return True
            
        except Exception as e:
            print(f"Error handling subscription creation: {e}")
            return False
    
    async def _handle_subscription_cancelled(self, data: Dict[str, Any]) -> bool:
        """Handle subscription cancellation"""
        email = data.get("customer", {}).get("email")
        subscription_code = data.get("subscription_code")
        
        if not email:
            return False
        
        try:
            db = self._get_db()
            
            # Update user's pro status
            auth_service.update_user_pro_status(email, False)
            
            # Update subscription record
            db.table("subscriptions").update({
                "status": "cancelled",
                "cancelled_at": datetime.utcnow().isoformat()
            }).eq("paystack_subscription_code", subscription_code).execute()
            
            # Send cancellation email
            email_service.send_subscription_cancelled(email)
            
            return True
            
        except Exception as e:
            print(f"Error handling subscription cancellation: {e}")
            return False
    
    async def _handle_payment_failed(self, data: Dict[str, Any]) -> bool:
        """Handle failed payment"""
        # For now, just log it
        # You might want to send a notification email
        return True
    
    async def _log_payment_event(self, event_type: str, data: Dict[str, Any]):
        """Log payment event to database"""
        try:
            db = self._get_db()
            
            db.table("payment_events").insert({
                "event_type": event_type,
                "paystack_reference": data.get("reference"),
                "email": data.get("customer", {}).get("email"),
                "amount": data.get("amount"),
                "currency": data.get("currency"),
                "status": data.get("status"),
                "raw_payload": data
            }).execute()
            
        except Exception as e:
            print(f"Error logging payment event: {e}")
    
    # ==================
    # Subscription Management
    # ==================
    
    async def get_subscription_status(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user's subscription status.
        
        Args:
            email: User's email
            
        Returns:
            Subscription info
        """
        try:
            db = self._get_db()
            
            result = db.table("users").select(
                "id, email, is_pro, paystack_subscription_code"
            ).eq("email", email.lower()).single().execute()
            
            if not result.data:
                return None
            
            user_data = result.data
            
            # Get subscription details if exists
            if user_data.get("paystack_subscription_code"):
                sub_result = db.table("subscriptions").select("*").eq(
                    "paystack_subscription_code", 
                    user_data["paystack_subscription_code"]
                ).single().execute()
                
                if sub_result.data:
                    user_data["subscription"] = sub_result.data
            
            return user_data
            
        except Exception as e:
            print(f"Error getting subscription status: {e}")
            return None
    
    async def cancel_subscription(self, subscription_code: str) -> bool:
        """
        Cancel a Paystack subscription.
        
        Args:
            subscription_code: Paystack subscription code
            
        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.PAYSTACK_API_URL}/subscription/disable",
                    json={
                        "code": subscription_code,
                        "token": subscription_code  # Email token from subscription
                    },
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return data.get("status", False)
                
        except Exception as e:
            print(f"Error cancelling subscription: {e}")
            return False


# Singleton instance
payment_service = PaymentService()
