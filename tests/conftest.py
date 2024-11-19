import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from main import app
from core.dependencies import get_db
from db.engine import Base
from models import User, Post, Comment
from modules.comment.schemas import CommentCreate
from modules.comment.services import CommentService


# URL test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture(scope="function")
def db_session():

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


# @pytest.fixture(autouse=True)
# def clear_tables(db_session: Session):
#     db_session.query(User).delete()
#     db_session.query(Post).delete()
#     db_session.commit()


@pytest.fixture
def test_user(db_session: Session):

    user = User(email="test@example.com", hashed_password="hashed_password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_post(db_session: Session, test_user):

    post = Post(title="Test Post", content="Test Content", owner_id=test_user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


@pytest.fixture
def test_comment(db_session: Session, test_user, test_post):
    comment = Comment(content="Test Comment", post_id=test_post.id, owner_id=test_user.id)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)
    return comment


@pytest.fixture
def test_comment_data():
    return CommentCreate(content="Test comment content")


@pytest.fixture
def comment_service(db_session: Session):
    return CommentService(db=db_session)


@pytest.fixture(autouse=True)
def clear_tables(db_session: Session):
    """
    Очищення таблиць User, Post та Comment перед кожним тестом.
    """
    db_session.query(Comment).delete()
    db_session.query(Post).delete()
    db_session.query(User).delete()
    db_session.commit()
