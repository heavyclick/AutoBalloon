"""
AutoBalloon Backend
FastAPI application for manufacturing blueprint dimension detection
Updated with:
- Multi-page PDF support
- Download routes for ballooned PDF/ZIP/Images
- Glass Wall system (guest sessions, payments v2)
- Promo code redemption
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import CORS_ORIGINS, APP_NAME, APP_VERSION
from datetime import datetime, timedelta
import httpx
import os

app = FastAPI(
    title=f"{APP_NAME} API",
    description="Automatic dimension ballooning for manufacturing blueprints",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from api.routes import router as main_router
from api.auth_routes import router as auth_router
from api.payment_routes import router as payment_router
from api.usage_routes import router as usage_router
from api.history_routes import router as history_router
from api.download_routes import router as download_router

# Glass Wall routes
from api.guest_session_routes import router as guest_session_router
from api.payment_routes_v2 import router as payment_router_v2

# Include existing routers
app.include_router(main_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(usage_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(download_router)

# Include Glass Wall routers
app.include_router(guest_session_router, prefix="/api")
app.include_router(payment_router_v2, prefix="/api")


# =============================================================================
# VALID PROMO CODES - Edit this list to add/remove promo codes
# =============================================================================

VALID_PROMO_CODES = {
    "LINKEDIN24": {"hours": 24, "type": "linkedin_promo", "max_redemptions": 1000, "daily_cap": 20},
    "INFLUENCER": {"hours": 24, "type": "influencer", "max_redemptions": 500, "daily_cap": 30},
    "TWITTER24": {"hours": 24, "type": "twitter_promo", "max_redemptions": 1000, "daily_cap": 20},
    "LAUNCH50": {"hours": 48, "type": "launch_promo", "max_redemptions": 200, "daily_cap": 50},
    # Lifetime access codes for micro-influencers (limited quantity)
    "CREATOR2025": {"hours": None, "type": "lifetime_influencer", "max_redemptions": 50, "daily_cap": 75, "monthly_cap": 300},
    "IGPARTNER": {"hours": None, "type": "lifetime_influencer", "max_redemptions": 25, "daily_cap": 75, "monthly_cap": 300},
    "YTPARTNER": {"hours": None, "type": "lifetime_influencer", "max_redemptions": 25, "daily_cap": 75, "monthly_cap": 300},
    # Add more codes here as needed
}

# Usage caps by plan type
USAGE_CAPS = {
    "linkedin_promo": {"daily": 20, "monthly": None},
    "twitter_promo": {"daily": 20, "monthly": None},
    "influencer": {"daily": 30, "monthly": None},
    "launch_promo": {"daily": 50, "monthly": None},
    "lifetime_influencer": {"daily": 75, "monthly": 300},
    "pass_24h": {"daily": 50, "monthly": None},
    "pro_monthly": {"daily": 100, "monthly": 500},
    "free": {"daily": 3, "monthly": 5},  # Free tier
}


# =============================================================================
# PROMO ROUTES
# =============================================================================

def get_supabase_client():
    """Get Supabase client - inline to avoid import issues"""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    return create_client(url, key)


def send_welcome_email(email: str, hours: int):
    """Send welcome email via Resend"""
    import resend
    
    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        print("WARNING: RESEND_API_KEY not set, skipping email")
        return False
    
    try:
        resend.Emails.send({
            "from": "AutoBalloon <hello@autoballoon.space>",
            "to": email,
            "subject": f"🎉 Your {hours}-Hour Free Access is Active!",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #E63946;">Welcome to AutoBalloon! 🎈</h1>
                
                <p>Great news! Your <strong>{hours}-hour free access</strong> is now active.</p>
                
                <p>You can now:</p>
                <ul>
                    <li>✅ Upload unlimited blueprints</li>
                    <li>✅ Download ballooned PDFs</li>
                    <li>✅ Export AS9102 Form 3 Excel reports</li>
                </ul>
                
                <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                    <p style="margin: 0 0 10px 0; color: #666;">Ready to start?</p>
                    <a href="https://autoballoon.space" 
                       style="display: inline-block; background: #E63946; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Open AutoBalloon →
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    Your access expires in {hours} hours. After that, you can upgrade to Pro for unlimited access.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p style="color: #999; font-size: 12px;">
                    Questions? Reply to this email or reach out at hello@autoballoon.space
                </p>
            </div>
            """
        })
        print(f"Welcome email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_lifetime_welcome_email(email: str):
    """Send lifetime access welcome email via Resend"""
    import resend
    
    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        print("WARNING: RESEND_API_KEY not set, skipping email")
        return False
    
    try:
        resend.Emails.send({
            "from": "AutoBalloon <hello@autoballoon.space>",
            "to": email,
            "subject": "🎉 Welcome to AutoBalloon Pro - Lifetime Access!",
            "html": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #E63946;">Welcome to the AutoBalloon Family! 🎈</h1>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                    <p style="color: white; font-size: 24px; font-weight: bold; margin: 0;">
                        ✨ LIFETIME PRO ACCESS ✨
                    </p>
                </div>
                
                <p>Thank you for being an amazing creator! As a valued partner, you now have <strong>lifetime Pro access</strong> to AutoBalloon.</p>
                
                <p>Your Pro benefits include:</p>
                <ul>
                    <li>✅ Unlimited blueprint processing forever</li>
                    <li>✅ AS9102 Form 3 Excel exports</li>
                    <li>✅ Priority processing</li>
                    <li>✅ All future features included</li>
                </ul>
                
                <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                    <p style="margin: 0 0 10px 0; color: #666;">Ready to start?</p>
                    <a href="https://autoballoon.space" 
                       style="display: inline-block; background: #E63946; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Open AutoBalloon →
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    We'd love to see your content! Tag us when you share and we'll reshare your posts. 🙌
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p style="color: #999; font-size: 12px;">
                    Questions? Reply to this email - we're always here to help!
                </p>
            </div>
            """
        })
        print(f"Lifetime welcome email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send lifetime email: {e}")
        return False


@app.post("/api/promo/redeem")
async def redeem_promo(request: Request):
    """
    Frontend sends: {"email": "user@example.com", "promo_code": "LINKEDIN24"}
    Backend grants 24h access and returns success
    """
    try:
        db = get_supabase_client()
        
        data = await request.json()
        email = data.get("email", "").lower().strip()
        code = data.get("promo_code", "").upper().strip()
        
        print(f"Promo redeem attempt: email={email}, code={code}")
        
        # Validate email
        if not email or "@" not in email:
            return JSONResponse({"success": False, "message": "Invalid email"}, status_code=400)
        
        # Check if promo code exists
        if code not in VALID_PROMO_CODES:
            return JSONResponse({"success": False, "message": "Invalid promo code"}, status_code=400)
        
        promo = VALID_PROMO_CODES[code]
        
        # Check if this email already used this promo type (prevent re-use)
        existing_for_email = db.table("access_passes").select("id").eq("email", email).eq("pass_type", promo["type"]).execute()
        if existing_for_email.data and len(existing_for_email.data) > 0:
            return JSONResponse({
                "success": False, 
                "message": "You've already used this type of promo code"
            }, status_code=400)
        
        # Check if promo code has reached max redemptions
        if "max_redemptions" in promo:
            total_redemptions = db.table("access_passes").select("id", count="exact").eq("granted_by", f"promo_{code}").execute()
            if total_redemptions.count >= promo["max_redemptions"]:
                return JSONResponse({
                    "success": False, 
                    "message": "This promo code has reached its limit. Try another code or upgrade to Pro!"
                }, status_code=400)
        
        # Handle lifetime vs timed access
        if promo["hours"] is None:
            expires_at = None
            hours_display = "lifetime"
        else:
            expires_at = (datetime.utcnow() + timedelta(hours=promo["hours"])).isoformat()
            hours_display = promo["hours"]
        
        # Grant access
        insert_data = {
            "email": email,
            "pass_type": promo["type"],
            "granted_by": f"promo_{code}",
            "is_active": True
        }
        if expires_at:
            insert_data["expires_at"] = expires_at
        
        result = db.table("access_passes").insert(insert_data).execute()
        
        print(f"Promo redeemed successfully for {email}: {result}")
        
        # Send welcome email
        if promo["hours"] is None:
            send_lifetime_welcome_email(email)
        else:
            send_welcome_email(email, promo["hours"])
        
        # Determine message based on access type
        if promo["hours"] is None:
            message = "Success! You now have lifetime Pro access."
        else:
            message = f"Success! You have {promo['hours']} hours of free access."
        
        return {
            "success": True,
            "message": message,
            "expires_at": expires_at,
            "hours": promo["hours"],
            "is_lifetime": promo["hours"] is None,
            "daily_cap": promo.get("daily_cap", USAGE_CAPS.get(promo["type"], {}).get("daily", 50))
        }
        
    except Exception as e:
        print(f"Promo error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"success": False, "message": f"Server error: {str(e)}"}, status_code=500)


@app.get("/api/access/check")
async def check_access(email: str = ""):
    """
    Frontend calls: GET /api/access/check?email=user@example.com
    Returns: {"has_access": true/false, "expires_at": "...", ...}
    """
    if not email:
        return {"has_access": False}
    
    try:
        db = get_supabase_client()
        email = email.lower().strip()
        
        # Query using Supabase client
        result = db.table("access_passes").select("pass_type, expires_at, granted_by").eq("email", email).eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            row = result.data[0]
            # Check if not expired
            if row.get("expires_at"):
                expires = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
                if expires < datetime.now(expires.tzinfo):
                    return {"has_access": False, "reason": "expired"}
            
            # Get usage caps for this plan type
            caps = USAGE_CAPS.get(row["pass_type"], {"daily": 50, "monthly": 500})
            
            return {
                "has_access": True,
                "access_type": row["pass_type"],
                "expires_at": row["expires_at"],
                "daily_cap": caps.get("daily"),
                "monthly_cap": caps.get("monthly")
            }
        
        return {"has_access": False}
        
    except Exception as e:
        print(f"Access check error: {type(e).__name__}: {e}")
        return {"has_access": False, "error": str(e)}


@app.post("/api/usage/track")
async def track_usage(request: Request):
    """
    Track when a user processes a drawing.
    Called after successful processing.
    """
    try:
        db = get_supabase_client()
        data = await request.json()
        email = data.get("email", "").lower().strip()
        
        if not email:
            return {"success": False, "message": "Email required"}
        
        # Get user's access pass
        access = db.table("access_passes").select("id, pass_type").eq("email", email).eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        
        if not access.data:
            return {"success": False, "message": "No active access"}
        
        pass_type = access.data[0]["pass_type"]
        access_id = access.data[0]["id"]
        
        # Record the usage
        db.table("usage_logs").insert({
            "email": email,
            "access_pass_id": str(access_id),
            "action": "process_drawing",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        return {"success": True}
        
    except Exception as e:
        print(f"Usage track error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/usage/status")
async def get_usage_status(email: str = ""):
    """
    Get current usage status for a user.
    Returns daily/monthly counts and remaining allowance.
    """
    if not email:
        return {"error": "Email required"}
    
    try:
        db = get_supabase_client()
        email = email.lower().strip()
        
        # Get user's access pass
        access = db.table("access_passes").select("pass_type, expires_at").eq("email", email).eq("is_active", True).order("created_at", desc=True).limit(1).execute()
        
        if not access.data:
            return {
                "has_access": False,
                "daily_used": 0,
                "monthly_used": 0,
                "daily_cap": USAGE_CAPS["free"]["daily"],
                "monthly_cap": USAGE_CAPS["free"]["monthly"]
            }
        
        pass_type = access.data[0]["pass_type"]
        caps = USAGE_CAPS.get(pass_type, {"daily": 50, "monthly": 500})
        
        # Count today's usage
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        daily_usage = db.table("usage_logs").select("id", count="exact").eq("email", email).gte("created_at", today_start).execute()
        
        # Count this month's usage
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        monthly_usage = db.table("usage_logs").select("id", count="exact").eq("email", email).gte("created_at", month_start).execute()
        
        daily_used = daily_usage.count or 0
        monthly_used = monthly_usage.count or 0
        
        daily_cap = caps.get("daily") or 999
        monthly_cap = caps.get("monthly") or 9999
        
        # Check if user has exceeded limits
        exceeded = False
        exceeded_reason = None
        
        if daily_used >= daily_cap:
            exceeded = True
            exceeded_reason = f"Daily limit reached ({daily_cap} drawings). Resets at midnight UTC."
        elif monthly_cap and monthly_used >= monthly_cap:
            exceeded = True
            exceeded_reason = f"Monthly limit reached ({monthly_cap} drawings). Resets on the 1st."
        
        return {
            "has_access": True,
            "pass_type": pass_type,
            "daily_used": daily_used,
            "daily_cap": daily_cap,
            "daily_remaining": max(0, daily_cap - daily_used),
            "monthly_used": monthly_used,
            "monthly_cap": monthly_cap,
            "monthly_remaining": max(0, monthly_cap - monthly_used) if monthly_cap else None,
            "exceeded": exceeded,
            "exceeded_reason": exceeded_reason
        }
        
    except Exception as e:
        print(f"Usage status error: {e}")
        return {"error": str(e)}


@app.get("/api/usage/can-process")
async def can_process(email: str = ""):
    """
    Quick check if user can process another drawing.
    Returns simple yes/no with reason.
    """
    if not email:
        return {"can_process": False, "reason": "Not logged in"}
    
    try:
        status = await get_usage_status(email)
        
        if status.get("error"):
            return {"can_process": False, "reason": status["error"]}
        
        if not status.get("has_access"):
            return {"can_process": False, "reason": "No active access. Use a promo code or upgrade to Pro."}
        
        if status.get("exceeded"):
            return {"can_process": False, "reason": status["exceeded_reason"]}
        
        return {
            "can_process": True,
            "daily_remaining": status["daily_remaining"],
            "monthly_remaining": status.get("monthly_remaining")
        }
        
    except Exception as e:
        print(f"Can process check error: {e}")
        return {"can_process": False, "reason": "Error checking usage"}


# =============================================================================
# STANDARD ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api")
async def api_root():
    return {
        "name": f"{APP_NAME} API",
        "version": APP_VERSION,
        "endpoints": [
            # Processing
            "/api/process",
            "/api/export",
            # Downloads
            "/download/pdf",
            "/download/zip", 
            "/download/image",
            "/download/excel",
            # Auth
            "/api/auth/magic-link",
            "/api/auth/verify",
            # Promo (NEW)
            "/api/promo/redeem",
            "/api/access/check",
            # Payments (original)
            "/api/payments/pricing",
            # Payments v2 (Glass Wall)
            "/api/payments/create-checkout",
            "/api/payments/webhook",
            "/api/payments/check-access",
            # Guest Sessions (Glass Wall)
            "/api/guest-session/save",
            "/api/guest-session/capture-email",
            "/api/guest-session/retrieve/{session_id}",
            # Usage
            "/api/usage/check",
            # History
            "/api/history"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
