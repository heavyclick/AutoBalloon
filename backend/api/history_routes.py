"""
History API Routes
Permanent history storage for Pro users
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.history_service import history_service
from services.auth_service import User
from api.auth_routes import require_auth, require_pro


router = APIRouter(prefix="/history", tags=["History"])


# ==================
# Request/Response Models
# ==================

class HistoryEntryRequest(BaseModel):
    """Request to add history entry"""
    filename: str
    thumbnail: str
    dimensions: List[Dict[str, Any]]
    image_data: str
    grid: Optional[Dict[str, Any]] = None
    processing_time_ms: int = 0


class HistoryEntryResponse(BaseModel):
    """History entry summary (for list view)"""
    id: str
    filename: str
    thumbnail: Optional[str]
    dimension_count: int
    created_at: str


class HistoryDetailResponse(BaseModel):
    """Full history entry details"""
    id: str
    filename: str
    thumbnail: Optional[str]
    dimensions: List[Dict[str, Any]]
    image_data: str
    grid: Optional[Dict[str, Any]]
    dimension_count: int
    processing_time_ms: Optional[int]
    created_at: str


class HistoryListResponse(BaseModel):
    """List of history entries"""
    entries: List[HistoryEntryResponse]
    total: int


class HistorySettingsRequest(BaseModel):
    """Request to update history settings"""
    enabled: bool


class HistorySettingsResponse(BaseModel):
    """History settings response"""
    enabled: bool


# ==================
# Endpoints
# ==================

@router.get("", response_model=HistoryListResponse)
async def get_history(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(require_pro)
):
    """
    Get user's history entries.
    Requires Pro subscription.
    """
    entries = history_service.get_user_history(user.id, limit, offset)
    total = history_service.get_history_count(user.id)
    
    return HistoryListResponse(
        entries=[HistoryEntryResponse(**entry) for entry in entries],
        total=total
    )


@router.post("", response_model=HistoryEntryResponse)
async def add_history_entry(
    request: HistoryEntryRequest,
    user: User = Depends(require_pro)
):
    """
    Add a new history entry.
    Requires Pro subscription.
    """
    # Check if history is enabled for user
    if not history_service.get_history_enabled(user.id):
        raise HTTPException(status_code=400, detail="History is disabled for this account")
    
    entry = history_service.add_entry(
        user_id=user.id,
        filename=request.filename,
        thumbnail=request.thumbnail,
        dimensions=request.dimensions,
        image_data=request.image_data,
        grid=request.grid,
        processing_time_ms=request.processing_time_ms
    )
    
    if entry:
        return HistoryEntryResponse(
            id=entry["id"],
            filename=entry["filename"],
            thumbnail=entry.get("thumbnail"),
            dimension_count=entry.get("dimension_count", 0),
            created_at=entry["created_at"]
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to save history entry")


@router.get("/{entry_id}", response_model=HistoryDetailResponse)
async def get_history_entry(
    entry_id: str,
    user: User = Depends(require_pro)
):
    """
    Get a specific history entry with full data.
    Requires Pro subscription.
    """
    entry = history_service.get_entry(user.id, entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    return HistoryDetailResponse(**entry)


@router.delete("/{entry_id}")
async def delete_history_entry(
    entry_id: str,
    user: User = Depends(require_pro)
):
    """
    Delete a history entry.
    Requires Pro subscription.
    """
    success = history_service.delete_entry(user.id, entry_id)
    
    if success:
        return {"success": True, "message": "Entry deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete entry")


@router.delete("")
async def clear_history(user: User = Depends(require_pro)):
    """
    Clear all history for the user.
    Requires Pro subscription.
    """
    success = history_service.clear_user_history(user.id)
    
    if success:
        return {"success": True, "message": "History cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear history")


@router.get("/settings/enabled", response_model=HistorySettingsResponse)
async def get_history_settings(user: User = Depends(require_auth)):
    """
    Get user's history settings.
    """
    enabled = history_service.get_history_enabled(user.id)
    return HistorySettingsResponse(enabled=enabled)


@router.put("/settings/enabled", response_model=HistorySettingsResponse)
async def update_history_settings(
    request: HistorySettingsRequest,
    user: User = Depends(require_auth)
):
    """
    Update user's history settings.
    """
    success = history_service.set_history_enabled(user.id, request.enabled)
    
    if success:
        return HistorySettingsResponse(enabled=request.enabled)
    else:
        raise HTTPException(status_code=500, detail="Failed to update settings")
