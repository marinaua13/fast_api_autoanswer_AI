from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from core.dependencies import get_db, get_current_user
from modules.post import schemas, crud

router = APIRouter()


@router.post("/", response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_post(db=db, post=post, user_id=current_user.id)


@router.get("/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.get_post(db, post_id=post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post
