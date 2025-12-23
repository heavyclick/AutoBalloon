"""
Database Service
Supabase client wrapper for database operations
"""
from typing import Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY


class DatabaseService:
    """Singleton wrapper for Supabase client"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client"""
        if cls._instance is None:
            if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                raise ValueError("Supabase credentials not configured")
            cls._instance = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset client (for testing)"""
        cls._instance = None


def get_db() -> Client:
    """Dependency injection helper"""
    return DatabaseService.get_client()
