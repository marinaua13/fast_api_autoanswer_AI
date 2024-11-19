from better_profanity import profanity
from sqlalchemy.orm import Session
from models import Comment
from modules.comment.schemas import CommentCreate

profanity.load_censor_words()


def create_comment(db: Session, comment_data: CommentCreate, user_id: int, post_id: int, is_blocked: bool):
    new_comment = Comment(
        content=comment_data.content,
        post_id=post_id,
        owner_id=user_id,
        is_blocked=is_blocked
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


def get_comment_by_id(db: Session, comment_id: int):
    return db.query(Comment).filter(Comment.id == comment_id).first()
