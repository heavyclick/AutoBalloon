"""
Authentication Service
Handles magic link generation, verification, and JWT tokens
"""
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel

from services.database_service import get_db
from services.email_service import email_service
from config import (
    JWT_SECRET, 
    JWT_ALGORITHM, 
    JWT_EXPIRATION_HOURS,
    MAGIC_LINK_EXPIRATION_MINUTES,
    APP_URL
)


class User(BaseModel):
    """User model"""
    id: str
    email: str
    is_pro: bool = False
    history_enabled: bool = True
    created_at: Optional[str] = None


class AuthService:
    """
    Authentication service using magic links (passwordless).
    """
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        """Lazy load database client"""
        if self.db is None:
            self.db = get_db()
        return self.db
    
    # ==================
    # Magic Link Methods
    # ==================
    
    def create_magic_link(self, email: str) -> Optional[str]:
        """
        Create a magic link token and send it via email.
        
        Args:
            email: User's email address
            
        Returns:
            Token string if successful, None otherwise
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Set expiration
        expires_at = datetime.utcnow() + timedelta(minutes=MAGIC_LINK_EXPIRATION_MINUTES)
        
        try:
            db = self._get_db()
            
            # Invalidate any existing unused tokens for this email
            db.table("magic_links").update({
                "used": True
            }).eq("email", email.lower()).eq("used", False).execute()
            
            # Insert new token
            db.table("magic_links").insert({
                "email": email.lower(),
                "token": token,
                "expires_at": expires_at.isoformat(),
                "used": False
            }).execute()
            
            # Send email
            if email_service.send_magic_link(email, token):
                return token
            
            return None
            
        except Exception as e:
            print(f"Error creating magic link: {e}")
            return None
    
    def verify_magic_link(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a magic link token and return user + JWT.
        
        Args:
            token: Magic link token
            
        Returns:
            Dict with user and access_token, or None if invalid
        """
        try:
            db = self._get_db()
            
            # Find the token
            result = db.table("magic_links").select("*").eq(
                "token", token
            ).eq("used", False).single().execute()
            
            if not result.data:
                return None
            
            magic_link = result.data
            
            # Check expiration
            expires_at = datetime.fromisoformat(magic_link["expires_at"].replace("Z", "+00:00"))
            if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                return None
            
            # Mark token as used
            db.table("magic_links").update({
                "used": True
            }).eq("id", magic_link["id"]).execute()
            
            # Get or create user
            email = magic_link["email"]
            user = self.get_or_create_user(email)
            
            if not user:
                return None
            
            # Generate JWT
            access_token = self.create_access_token(user)
            
            return {
                "user": user.model_dump(),
                "access_token": access_token
            }
            
        except Exception as e:
            print(f"Error verifying magic link: {e}")
            return None
    
    # ==================
    # User Methods
    # ==================
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email
            
        Returns:
            User object or None
        """
        try:
            db = self._get_db()
            result = db.table("users").select("*").eq(
                "email", email.lower()
            ).single().execute()
            
            if result.data:
                return User(**result.data)
            return None
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User object or None
        """
        try:
            db = self._get_db()
            result = db.table("users").select("*").eq(
                "id", user_id
            ).single().execute()
            
            if result.data:
                return User(**result.data)
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_or_create_user(self, email: str) -> Optional[User]:
        """
        Get existing user or create new one.
        
        Args:
            email: User's email
            
        Returns:
            User object
        """
        # Try to get existing user
        user = self.get_user_by_email(email)
        if user:
            return user
        
        # Create new user
        try:
            db = self._get_db()
            result = db.table("users").insert({
                "email": email.lower(),
                "is_pro": False,
                "history_enabled": True
            }).execute()
            
            if result.data:
                return User(**result.data[0])
            return None
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def update_user_pro_status(self, email: str, is_pro: bool, paystack_customer_code: str = None) -> bool:
        """
        Update user's Pro subscription status.
        
        Args:
            email: User's email
            is_pro: New Pro status
            paystack_customer_code: Paystack customer code
            
        Returns:
            True if successful
        """
        try:
            db = self._get_db()
            
            update_data = {"is_pro": is_pro}
            if paystack_customer_code:
                update_data["paystack_customer_code"] = paystack_customer_code
            
            db.table("users").update(update_data).eq(
                "email", email.lower()
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error updating user pro status: {e}")
            return False
    
    # ==================
    # JWT Methods
    # ==================
    
    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token for user.
        
        Args:
            user: User object
            
        Returns:
            JWT token string
        """
        expires = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            "sub": user.id,
            "email": user.email,
            "is_pro": user.is_pro,
            "exp": expires,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT access token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User object or None
        """
        payload = self.verify_access_token(token)
        if not payload:
            return None
        
        return self.get_user_by_id(payload["sub"])


# Singleton instance
auth_service = AuthService()
