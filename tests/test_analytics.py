from sqlalchemy.orm import Session
from datetime import datetime
from modules.analytics.services import get_comments_breakdown
from models import Comment


def test_get_comments_breakdown_success(db_session: Session, test_post, test_user):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    comment1 = Comment(content="Test Comment 1", post_id=test_post.id, owner_id=test_user.id, created_at=today)
    comment2 = Comment(content="Test Comment 2", post_id=test_post.id, owner_id=test_user.id, created_at=today)
    comment3 = Comment(content="Blocked Comment 1", post_id=test_post.id, owner_id=test_user.id, created_at=today,
                       is_blocked=True)
    comment4 = Comment(content="Blocked Comment 2", post_id=test_post.id, owner_id=test_user.id, created_at=today,
                       is_blocked=True)

    db_session.add_all([comment1, comment2, comment3, comment4])
    db_session.commit()

    result = get_comments_breakdown(
        date_from=today.strftime("%Y-%m-%d"),
        date_to=today.strftime("%Y-%m-%d"),
        db=db_session
    )

    assert len(result) == 1
    assert result[0]["total_comments"] == 4
    assert result[0]["blocked_comments"] == 2

