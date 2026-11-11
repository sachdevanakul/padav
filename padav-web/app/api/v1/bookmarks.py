from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import BookmarkServiceDep, CurrentUser
from app.schemas.bookmark import BookmarkCreate, BookmarkOut

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/", response_model=List[BookmarkOut])
def list_bookmarks(current_user: CurrentUser, service: BookmarkServiceDep):
    return service.list(current_user)


@router.post("/", response_model=BookmarkOut)
def create_bookmark(bookmark_in: BookmarkCreate, current_user: CurrentUser, service: BookmarkServiceDep):
    return service.create(current_user, bookmark_in)


@router.delete("/{bookmark_id}")
def delete_bookmark(bookmark_id: str, current_user: CurrentUser, service: BookmarkServiceDep):
    service.delete(current_user, bookmark_id)
    return {"message": "Bookmark deleted"}
