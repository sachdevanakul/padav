from fastapi import APIRouter, HTTPException
from typing import List

from app.core.dependencies import DbSession, CurrentUser
from app.models.bookmark import Bookmark
from app.schemas.bookmark import BookmarkOut, BookmarkBase

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/", response_model=List[BookmarkOut])
def list_bookmarks(current_user: CurrentUser, db: DbSession):
    """List user's bookmarks."""
    return db.query(Bookmark).filter(Bookmark.user_id == current_user.id).all()


@router.post("/", response_model=BookmarkOut)
def create_bookmark(
    bookmark_in: BookmarkBase,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a bookmark."""
    bookmark = Bookmark(user_id=current_user.id, **bookmark_in.model_dump())
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{bookmark_id}")
def delete_bookmark(bookmark_id: str, current_user: CurrentUser, db: DbSession):
    """Delete a bookmark."""
    bookmark = (
        db.query(Bookmark)
        .filter(Bookmark.id == bookmark_id, Bookmark.user_id == current_user.id)
        .first()
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark deleted"}
