import asyncio
import os
import models
import schemas
import crud
import google.generativeai as genai

from db.engine import engine, Base
from better_profanity import profanity
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import BackgroundTasks
from datetime import datetime
from sqlalchemy import func, case
from dotenv import load_dotenv

app = FastAPI()

# Loading settings from .env file
load_dotenv()

# Configuration of environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
genai.configure(api_key=API_KEY)

# Initialize the database
Base.metadata.create_all(bind=engine)

# Loading words for censorship
profanity.load_censor_words()

# Model for generating responses
model = genai.GenerativeModel("gemini-1.5-flash")


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/posts/", response_model=schemas.Post)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db),
                current_user: schemas.User = Depends(get_current_user)):
    if profanity.contains_profanity(post.content):
        raise HTTPException(status_code=400, detail="Post contains inappropriate language.")

    return crud.create_post(db=db, post=post, user_id=current_user.id)


async def auto_reply(comment, db_engine, delay: int):
    await asyncio.sleep(delay)

    if comment.is_blocked:
        return

    response = model.generate_content(f"Reply to this comment: {comment.content}")
    reply_content = response.text.strip()

    if reply_content:
        db = Session(bind=db_engine)
        try:
            reply = schemas.CommentCreate(content=reply_content, post_id=comment.post_id)
            crud.create_comment(db=db, comment=reply, user_id=comment.owner_id)
        finally:
            db.close()


@app.post("/comments/", response_model=schemas.Comment)
async def create_comment(
        comment: schemas.CommentCreate,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_user),
        background_tasks: BackgroundTasks = None
):

    is_blocked = profanity.contains_profanity(comment.content)

    # Automatic moderation through the model
    response = model.generate_content(f"Moderate this comment: {comment.content}")
    moderated_comment = response.text.strip()
    if moderated_comment and moderated_comment != comment.content:
        comment.content = moderated_comment

    db_post = crud.get_post(db, post_id=comment.post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = crud.create_comment(db=db, comment=comment, user_id=current_user.id, is_blocked=is_blocked)

    if not is_blocked:
        # Background task for automatic response
        background_tasks.add_task(auto_reply, new_comment, engine, comment.reply_delay)

    return new_comment


@app.get("/comments-daily-breakdown/")
def get_comments_breakdown(
    date_from: str,
    date_to: str,
    db: Session = Depends(get_db)
):
    try:
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    daily_comments = (
        db.query(
            func.date(models.Comment.created_at).label('date'),
            func.count(models.Comment.id).label('total_comments'),
            func.sum(case((models.Comment.is_blocked == True, 1), else_=0)).label('blocked_comments')
        )
        .filter(models.Comment.created_at >= start_date,
                models.Comment.created_at <= end_date)  # Ось тут замість between
        .group_by(func.date(models.Comment.created_at))
        .all()
    )

    return [
        {
            "date": record.date,
            "total_comments": record.total_comments,
            "blocked_comments": record.blocked_comments
        } for record in daily_comments
    ]
