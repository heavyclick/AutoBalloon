"""
History Service
Manages permanent history storage for Pro users
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from services.database_service import get_db


class HistoryService:
    """
    History service for Pro users.
    
    Free users: localStorage with 7-day TTL (handled by frontend)
    Pro users: Permanent database storage (this service)
    """
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        """Lazy load database client"""
        if self.db is None:
            self.db = get_db()
        return self.db
    
    # ==================
    # CRUD Operations
    # ==================
    
    def add_entry(
        self,
        user_id: str,
        filename: str,
        thumbnail: str,
        dimensions: List[Dict],
        image_data: str,
        grid: Optional[Dict] = None,
        processing_time_ms: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Add a new history entry.
        
        Args:
            user_id: User's UUID
            filename: Original filename
            thumbnail: Base64 thumbnail or URL
            dimensions: List of dimension objects
            image_data: Base64 image or URL
            grid: Grid detection data
            processing_time_ms: Processing time
            
        Returns:
            Created entry or None
        """
        try:
            db = self._get_db()
            
            result = db.table("history").insert({
                "user_id": user_id,
                "filename": filename,
                "thumbnail": thumbnail,
                "dimensions": dimensions,
                "image_data": image_data,
                "grid": grid,
                "dimension_count": len(dimensions),
                "processing_time_ms": processing_time_ms
            }).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error adding history entry: {e}")
            return None
    
    def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's history entries.
        
        Args:
            user_id: User's UUID
            limit: Max entries to return
            offset: Pagination offset
            
        Returns:
            List of history entries (newest first)
        """
        try:
            db = self._get_db()
            
            result = db.table("history").select(
                "id, filename, thumbnail, dimension_count, created_at"
            ).eq(
                "user_id", user_id
            ).order(
                "created_at", desc=True
            ).range(
                offset, offset + limit - 1
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []
    
    def get_entry(self, user_id: str, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific history entry with full data.
        
        Args:
            user_id: User's UUID (for ownership verification)
            entry_id: History entry ID
            
        Returns:
            Full history entry or None
        """
        try:
            db = self._get_db()
            
            result = db.table("history").select("*").eq(
                "id", entry_id
            ).eq(
                "user_id", user_id  # Verify ownership
            ).single().execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            print(f"Error getting history entry: {e}")
            return None
    
    def delete_entry(self, user_id: str, entry_id: str) -> bool:
        """
        Delete a history entry.
        
        Args:
            user_id: User's UUID (for ownership verification)
            entry_id: History entry ID
            
        Returns:
            True if deleted
        """
        try:
            db = self._get_db()
            
            # Verify ownership and delete
            db.table("history").delete().eq(
                "id", entry_id
            ).eq(
                "user_id", user_id
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting history entry: {e}")
            return False
    
    def clear_user_history(self, user_id: str) -> bool:
        """
        Clear all history for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if cleared
        """
        try:
            db = self._get_db()
            
            db.table("history").delete().eq(
                "user_id", user_id
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False
    
    def get_history_count(self, user_id: str) -> int:
        """
        Get total history count for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Total entry count
        """
        try:
            db = self._get_db()
            
            result = db.table("history").select(
                "id", count="exact"
            ).eq("user_id", user_id).execute()
            
            return result.count or 0
            
        except Exception as e:
            print(f"Error getting history count: {e}")
            return 0
    
    # ==================
    # User Settings
    # ==================
    
    def get_history_enabled(self, user_id: str) -> bool:
        """
        Check if user has history enabled.
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if history is enabled
        """
        try:
            db = self._get_db()
            
            result = db.table("users").select(
                "history_enabled"
            ).eq("id", user_id).single().execute()
            
            return result.data.get("history_enabled", True) if result.data else True
            
        except Exception as e:
            print(f"Error getting history setting: {e}")
            return True
    
    def set_history_enabled(self, user_id: str, enabled: bool) -> bool:
        """
        Enable/disable history for a user.
        
        Args:
            user_id: User's UUID
            enabled: New setting
            
        Returns:
            True if updated
        """
        try:
            db = self._get_db()
            
            db.table("users").update({
                "history_enabled": enabled
            }).eq("id", user_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Error setting history enabled: {e}")
            return False


# Singleton instance
history_service = HistoryService()
