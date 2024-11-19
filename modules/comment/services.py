import asyncio
from sqlalchemy.orm import Session
from modules.comment import schemas, crud
import google.generativeai as genai
from core.config import API_KEY
from moderation import check_profanity, censor_content


class CommentService:
    def __init__(self, db: Session):
        self.db = db
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def auto_reply(self, comment, delay: int):
        """Function for automatic reply to the comment."""
        await asyncio.sleep(delay)  # Wait for the specified delay

        if comment.is_blocked:
            return

        # Generate a response using AI
        response = self.model.generate_content(f"Reply to this comment: {comment.content}")
        reply_content = response.text.strip()

        if reply_content:
            reply = schemas.CommentCreate(content=reply_content, post_id=comment.post_id)
            is_blocked_reply = check_profanity(reply_content)

            crud.create_comment(
                db=self.db,
                comment_data=reply,
                user_id=comment.owner_id,
                post_id=comment.post_id,
                is_blocked=is_blocked_reply
            )

    def create_comment(self, comment: schemas.CommentCreate, user_id: int, post_id: int):
        """Create a comment with AI moderation."""
        is_blocked = check_profanity(comment.content)

        # Moderate the comment using AI
        response = self.model.generate_content(f"Moderate this comment: {comment.content}")
        moderated_content = response.text.strip()

        if moderated_content and moderated_content != comment.content:
            moderated_content = censor_content(moderated_content)
            comment.content = moderated_content

        # Call the CRUD function to create the comment in the DB
        new_comment = crud.create_comment(
            db=self.db,
            comment_data=comment,
            user_id=user_id,
            post_id=post_id,
            is_blocked=is_blocked
        )

        return new_comment
