import asyncio

import pytest
from sqlalchemy.orm import Session
from modules.comment.crud import create_comment
from models import User, Post, Comment
from modules.comment.schemas import CommentCreate
from modules.comment.services import CommentService
from unittest.mock import patch


def test_create_comment(db_session: Session, test_user: User, test_post: Post, test_comment_data):
    """
    Тест для створення коментаря через CRUD функцію
    """
    comment = create_comment(
        db=db_session,
        comment_data=test_comment_data,
        user_id=test_user.id,
        post_id=test_post.id,
        is_blocked=False
    )
    assert comment is not None
    assert comment.content == test_comment_data.content
    assert comment.post_id == test_post.id
    assert comment.owner_id == test_user.id
    assert comment.is_blocked is False


def test_service_create_comment(comment_service: CommentService, test_user: User, test_post: Post, test_comment_data):
    """
    Тест для створення коментаря через сервіс CommentService
    """
    created_comment = comment_service.create_comment(test_comment_data, user_id=test_user.id, post_id=test_post.id)

    assert created_comment is not None
    assert created_comment.content == test_comment_data.content
    assert created_comment.post_id == test_post.id
    assert created_comment.owner_id == test_user.id


@pytest.mark.asyncio
async def test_service_auto_reply(comment_service: CommentService, test_user: User, test_post: Post):
    comment_data = CommentCreate(content="Comment for auto reply test")

    created_comment = comment_service.create_comment(comment_data, user_id=test_user.id, post_id=test_post.id)

    # Мокаємо відповідь AI для функції auto_reply
    with patch.object(comment_service.model, "generate_content") as mock_generate_content:
        mock_generate_content.return_value.text = "Reply to this comment"

        await comment_service.auto_reply(created_comment, delay=0)

        # Додаємо невелике очікування, щоб дати час на виконання асинхронної функції
        await asyncio.sleep(0.1)

        # Перевірка репліки
        reply_comment = comment_service.db.query(Comment).filter(Comment.post_id == test_post.id).order_by(
            Comment.id.desc()).first()

        assert reply_comment is not None
        assert reply_comment.post_id == test_post.id
        assert reply_comment.owner_id == test_user.id
        assert "Reply to this comment" in reply_comment.content

        # Перевірка виклику мок-методу з фактичним текстом
        mock_generate_content.assert_called_once_with(f"Reply to this comment: {created_comment.content}")

@pytest.mark.parametrize("comment_content, expected_is_blocked, ai_moderated_text", [
    ("This is a clean comment", False, "This is a clean comment"),
    ("This is a sh*tty comment", True, "That comment is inappropriate.")
])
def test_service_create_comment_with_profanity(
    comment_service: CommentService,
    test_user,
    test_post,
    comment_content,
    expected_is_blocked,
    ai_moderated_text,
    db_session
):
    """
    Тестуємо створення коментаря з перевіркою на заборонені слова та AI модерацію.
    """
    test_comment_data = CommentCreate(content=comment_content)

    # Мокаємо метод profanity.contains_profanity та AI-модерацію
    with patch("modules.comment.services.profanity.contains_profanity") as mock_profanity_check, \
         patch.object(comment_service.model, "generate_content") as mock_generate_content:

        mock_profanity_check.return_value = expected_is_blocked
        mock_generate_content.return_value.text = ai_moderated_text

        created_comment = comment_service.create_comment(
            comment=test_comment_data,
            user_id=test_user.id,
            post_id=test_post.id
        )

        # Перевірка результату
        assert created_comment is not None
        assert created_comment.content == ai_moderated_text
        assert created_comment.is_blocked == expected_is_blocked

        # Перевіряємо виклики моків
        mock_profanity_check.assert_called_once_with(comment_content)
        mock_generate_content.assert_called_once_with(f"Moderate this comment: {comment_content}")
