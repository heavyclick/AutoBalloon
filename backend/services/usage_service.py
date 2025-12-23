"""
Usage Service
Tracks blueprint processing usage for free tier limits
"""
from datetime import datetime
from typing import Optional, Dict, Any

from services.database_service import get_db
from config import FREE_TIER_LIMIT


class UsageService:
    """
    Tracks usage for free tier limits.
    
    - Anonymous users: tracked by visitor_id (stored in localStorage)
    - Authenticated free users: tracked by user_id
    - Pro users: unlimited (no tracking needed)
    """
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        """Lazy load database client"""
        if self.db is None:
            self.db = get_db()
        return self.db
    
    def _get_current_month(self) -> str:
        """Get current month in YYYY-MM format"""
        return datetime.utcnow().strftime("%Y-%m")
    
    # ==================
    # Anonymous User Tracking
    # ==================
    
    def get_anonymous_usage(self, visitor_id: str) -> Dict[str, Any]:
        """
        Get usage count for anonymous user.
        
        Args:
            visitor_id: Unique visitor identifier from localStorage
            
        Returns:
            Dict with count, limit, and remaining
        """
        month_year = self._get_current_month()
        
        try:
            db = self._get_db()
            
            result = db.table("usage").select("count").eq(
                "visitor_id", visitor_id
            ).eq("month_year", month_year).single().execute()
            
            count = result.data["count"] if result.data else 0
            
            return {
                "count": count,
                "limit": FREE_TIER_LIMIT,
                "remaining": max(0, FREE_TIER_LIMIT - count),
                "can_process": count < FREE_TIER_LIMIT,
                "month": month_year
            }
            
        except Exception as e:
            # If no record exists, return 0 usage
            return {
                "count": 0,
                "limit": FREE_TIER_LIMIT,
                "remaining": FREE_TIER_LIMIT,
                "can_process": True,
                "month": month_year
            }
    
    def increment_anonymous_usage(self, visitor_id: str) -> Dict[str, Any]:
        """
        Increment usage count for anonymous user.
        
        Args:
            visitor_id: Unique visitor identifier
            
        Returns:
            Updated usage info
        """
        month_year = self._get_current_month()
        
        try:
            db = self._get_db()
            
            # Try to get existing record
            existing = db.table("usage").select("id, count").eq(
                "visitor_id", visitor_id
            ).eq("month_year", month_year).single().execute()
            
            if existing.data:
                # Update existing record
                new_count = existing.data["count"] + 1
                db.table("usage").update({
                    "count": new_count
                }).eq("id", existing.data["id"]).execute()
            else:
                # Create new record
                new_count = 1
                db.table("usage").insert({
                    "visitor_id": visitor_id,
                    "count": new_count,
                    "month_year": month_year
                }).execute()
            
            return {
                "count": new_count,
                "limit": FREE_TIER_LIMIT,
                "remaining": max(0, FREE_TIER_LIMIT - new_count),
                "can_process": new_count < FREE_TIER_LIMIT,
                "month": month_year
            }
            
        except Exception as e:
            print(f"Error incrementing anonymous usage: {e}")
            # Return conservative limit
            return {
                "count": FREE_TIER_LIMIT,
                "limit": FREE_TIER_LIMIT,
                "remaining": 0,
                "can_process": False,
                "month": month_year
            }
    
    # ==================
    # Authenticated User Tracking
    # ==================
    
    def get_user_usage(self, user_id: str, is_pro: bool = False) -> Dict[str, Any]:
        """
        Get usage count for authenticated user.
        
        Args:
            user_id: User's UUID
            is_pro: Whether user has Pro subscription
            
        Returns:
            Dict with count, limit, and remaining
        """
        # Pro users have unlimited usage
        if is_pro:
            return {
                "count": 0,
                "limit": None,  # Unlimited
                "remaining": None,
                "can_process": True,
                "is_pro": True,
                "month": self._get_current_month()
            }
        
        month_year = self._get_current_month()
        
        try:
            db = self._get_db()
            
            result = db.table("usage").select("count").eq(
                "user_id", user_id
            ).eq("month_year", month_year).single().execute()
            
            count = result.data["count"] if result.data else 0
            
            return {
                "count": count,
                "limit": FREE_TIER_LIMIT,
                "remaining": max(0, FREE_TIER_LIMIT - count),
                "can_process": count < FREE_TIER_LIMIT,
                "is_pro": False,
                "month": month_year
            }
            
        except Exception as e:
            return {
                "count": 0,
                "limit": FREE_TIER_LIMIT,
                "remaining": FREE_TIER_LIMIT,
                "can_process": True,
                "is_pro": False,
                "month": month_year
            }
    
    def increment_user_usage(self, user_id: str, is_pro: bool = False) -> Dict[str, Any]:
        """
        Increment usage count for authenticated user.
        
        Args:
            user_id: User's UUID
            is_pro: Whether user has Pro subscription
            
        Returns:
            Updated usage info
        """
        # Pro users don't need tracking
        if is_pro:
            return {
                "count": 0,
                "limit": None,
                "remaining": None,
                "can_process": True,
                "is_pro": True,
                "month": self._get_current_month()
            }
        
        month_year = self._get_current_month()
        
        try:
            db = self._get_db()
            
            # Try to get existing record
            existing = db.table("usage").select("id, count").eq(
                "user_id", user_id
            ).eq("month_year", month_year).single().execute()
            
            if existing.data:
                new_count = existing.data["count"] + 1
                db.table("usage").update({
                    "count": new_count
                }).eq("id", existing.data["id"]).execute()
            else:
                new_count = 1
                db.table("usage").insert({
                    "user_id": user_id,
                    "count": new_count,
                    "month_year": month_year
                }).execute()
            
            return {
                "count": new_count,
                "limit": FREE_TIER_LIMIT,
                "remaining": max(0, FREE_TIER_LIMIT - new_count),
                "can_process": new_count < FREE_TIER_LIMIT,
                "is_pro": False,
                "month": month_year
            }
            
        except Exception as e:
            print(f"Error incrementing user usage: {e}")
            return {
                "count": FREE_TIER_LIMIT,
                "limit": FREE_TIER_LIMIT,
                "remaining": 0,
                "can_process": False,
                "is_pro": False,
                "month": month_year
            }
    
    # ==================
    # Check Methods
    # ==================
    
    def can_process(self, visitor_id: str = None, user_id: str = None, is_pro: bool = False) -> bool:
        """
        Check if user can process another blueprint.
        
        Args:
            visitor_id: Anonymous user identifier
            user_id: Authenticated user ID
            is_pro: Whether user has Pro subscription
            
        Returns:
            True if within limits
        """
        if is_pro:
            return True
        
        if user_id:
            usage = self.get_user_usage(user_id, is_pro)
        elif visitor_id:
            usage = self.get_anonymous_usage(visitor_id)
        else:
            return False
        
        return usage.get("can_process", False)


# Singleton instance
usage_service = UsageService()
