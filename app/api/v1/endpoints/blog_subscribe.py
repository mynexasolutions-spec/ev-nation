from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.blog import BlogSubscriberCreate, BlogSubscriberRead
from app.services.blog_service import blog_service

router = APIRouter(prefix="/blog", tags=["blog"])


@router.post("/subscribe", response_model=BlogSubscriberRead, status_code=201)
def subscribe(payload: BlogSubscriberCreate, db: Session = Depends(get_db)):
    sub, created = blog_service.subscribe(db, payload.email)
    if not created:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already subscribed.")
    return sub
