from sqlalchemy.orm import Session
import models
import schemas
from passlib.context import CryptContext
from sqlalchemy import func, case
from models import Comment


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Function to hash the password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def create_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(**post.dict(), owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


# Content moderation
def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int, is_blocked: bool):
    db_comment = models.Comment(
        content=comment.content,
        post_id=comment.post_id,
        owner_id=user_id,
        is_blocked=is_blocked
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    return db_comment


def get_comments_breakdown(db: Session, date_from, date_to):
    results = (
        db.query(
            func.date(Comment.created_at).label("date"),
            func.count(Comment.id).label("total_comments"),
            func.sum(
                case([(Comment.is_blocked == True, 1)], else_=0)
            ).label("blocked_comments"),
        )
        .filter(Comment.created_at >= date_from, Comment.created_at <= date_to)
        .group_by(func.date(Comment.created_at))
        .order_by(func.date(Comment.created_at))
        .all()
    )

    return [{
        "date": str(result.date),
        "total_comments": result.total_comments,
        "blocked_comments": result.blocked_comments
    } for result in results]
