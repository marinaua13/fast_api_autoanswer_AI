from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from modules.comment import schemas
from core.dependencies import get_db, get_current_user
from modules.comment.services import CommentService
from models import User

router = APIRouter()


@router.post("/", response_model=schemas.CommentResponse)
async def create_comment(
    comment: schemas.CommentCreate,
    background_tasks: BackgroundTasks,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Initialize the comment service
    service = CommentService(db)

    # Create the comment with moderation
    new_comment = service.create_comment(comment, current_user.id, post_id)

    # Add a background task for auto-reply if the comment is not blocked
    if not new_comment.is_blocked and comment.reply_delay is not None:
        # This will start the automatic reply after the specified delay
        background_tasks.add_task(service.auto_reply, new_comment, comment.reply_delay)

    return new_comment
