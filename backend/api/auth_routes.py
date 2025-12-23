"""
Authentication API Routes
Magic link login and session management
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.auth_service import auth_service, User


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================
# Request/Response Models
# ==================

class MagicLinkRequest(BaseModel):
    """Request to send magic link"""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response after sending magic link"""
    success: bool
    message: str


class VerifyTokenRequest(BaseModel):
    """Request to verify magic link token"""
    token: str


class AuthResponse(BaseModel):
    """Response with user and access token"""
    success: bool
    user: Optional[dict] = None
    access_token: Optional[str] = None
    message: Optional[str] = None


class UserResponse(BaseModel):
    """Current user response"""
    id: str
    email: str
    is_pro: bool
    history_enabled: bool


# ==================
# Dependencies
# ==================

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """
    Dependency to get current user from JWT token.
    Returns None if not authenticated (doesn't raise error).
    """
    if not authorization:
        return None
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    return auth_service.get_current_user(token)


async def require_auth(authorization: Optional[str] = Header(None)) -> User:
    """
    Dependency that requires authentication.
    Raises 401 if not authenticated.
    """
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_pro(user: User = Depends(require_auth)) -> User:
    """
    Dependency that requires Pro subscription.
    Raises 403 if not Pro.
    """
    if not user.is_pro:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    return user


# ==================
# Endpoints
# ==================

@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(request: MagicLinkRequest):
    """
    Send a magic login link to the user's email.
    Creates account if doesn't exist.
    """
    token = auth_service.create_magic_link(request.email)
    
    if token:
        return MagicLinkResponse(
            success=True,
            message="Login link sent to your email. Check your inbox."
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send login link. Please try again."
        )


@router.post("/verify", response_model=AuthResponse)
async def verify_magic_link(request: VerifyTokenRequest):
    """
    Verify a magic link token and return JWT.
    """
    result = auth_service.verify_magic_link(request.token)
    
    if result:
        return AuthResponse(
            success=True,
            user=result["user"],
            access_token=result["access_token"]
        )
    else:
        return AuthResponse(
            success=False,
            message="Invalid or expired login link. Please request a new one."
        )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_auth)):
    """
    Get current authenticated user.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        is_pro=user.is_pro,
        history_enabled=user.history_enabled
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    Since we use JWTs, logout is handled client-side by removing the token.
    This endpoint exists for API completeness.
    """
    return {"success": True, "message": "Logged out successfully"}
