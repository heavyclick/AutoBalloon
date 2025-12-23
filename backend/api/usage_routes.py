"""
Usage API Routes
Track and check usage limits
"""
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import Optional

from services.usage_service import usage_service
from services.auth_service import User
from api.auth_routes import get_current_user
from config import FREE_TIER_LIMIT


router = APIRouter(prefix="/usage", tags=["Usage"])


# ==================
# Request/Response Models
# ==================

class UsageResponse(BaseModel):
    """Usage information response"""
    count: int
    limit: Optional[int]
    remaining: Optional[int]
    can_process: bool
    is_pro: bool = False
    month: str


class CheckUsageRequest(BaseModel):
    """Request to check usage (for anonymous users)"""
    visitor_id: str


# ==================
# Endpoints
# ==================

@router.get("/check", response_model=UsageResponse)
async def check_usage(
    visitor_id: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Check current usage.
    
    - Authenticated Pro users: unlimited
    - Authenticated free users: tracked by user_id
    - Anonymous users: tracked by visitor_id
    """
    if user:
        # Authenticated user
        usage = usage_service.get_user_usage(user.id, user.is_pro)
        return UsageResponse(
            count=usage["count"],
            limit=usage["limit"],
            remaining=usage["remaining"],
            can_process=usage["can_process"],
            is_pro=user.is_pro,
            month=usage["month"]
        )
    elif visitor_id:
        # Anonymous user
        usage = usage_service.get_anonymous_usage(visitor_id)
        return UsageResponse(
            count=usage["count"],
            limit=usage["limit"],
            remaining=usage["remaining"],
            can_process=usage["can_process"],
            is_pro=False,
            month=usage["month"]
        )
    else:
        # No identifier provided - return default free tier
        from datetime import datetime
        return UsageResponse(
            count=0,
            limit=FREE_TIER_LIMIT,
            remaining=FREE_TIER_LIMIT,
            can_process=True,
            is_pro=False,
            month=datetime.utcnow().strftime("%Y-%m")
        )


@router.post("/increment", response_model=UsageResponse)
async def increment_usage(
    visitor_id: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user)
):
    """
    Increment usage count after processing a blueprint.
    Called by the process endpoint after successful processing.
    """
    if user:
        usage = usage_service.increment_user_usage(user.id, user.is_pro)
        return UsageResponse(
            count=usage["count"],
            limit=usage["limit"],
            remaining=usage["remaining"],
            can_process=usage["can_process"],
            is_pro=user.is_pro,
            month=usage["month"]
        )
    elif visitor_id:
        usage = usage_service.increment_anonymous_usage(visitor_id)
        return UsageResponse(
            count=usage["count"],
            limit=usage["limit"],
            remaining=usage["remaining"],
            can_process=usage["can_process"],
            is_pro=False,
            month=usage["month"]
        )
    else:
        raise HTTPException(status_code=400, detail="visitor_id required for anonymous users")


from fastapi import HTTPException
