import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from main import app
from core.dependencies import get_db
from db.engine import Base, SessionLocal
from models import User, Post, Comment
from modules.comment.schemas import CommentCreate
from modules.comment.services import CommentService

# URL тестової бази даних
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Налаштовуємо engine для тестової БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Сесія для тестової БД
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Створюємо таблиці в тестовій базі перед запуском тестів
Base.metadata.create_all(bind=engine)

# Фікстура для створення тестового клієнта
@pytest.fixture(scope="module")
def client():
    """
    Фікстура для створення клієнта FastAPI з тестовою базою даних.
    """
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Замінюємо залежність get_db у додатку
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

# Фікстура для сесії БД
@pytest.fixture(scope="function")
def db_session():
    """
    Фікстура для створення нової сесії БД для кожного тесту.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Відкат змін після кожного тесту
        db.close()

# Фікстура для очищення таблиць перед кожним тестом
@pytest.fixture(autouse=True)
def clear_tables(db_session: Session):
    """
    Очищення таблиць User та Post перед кожним тестом.
    """
    db_session.query(User).delete()
    db_session.query(Post).delete()
    db_session.commit()

# Фікстура для створення тестового користувача
@pytest.fixture
def test_user(db_session: Session):
    """
    Створюємо тестового користувача для використання в тестах.
    """
    user = User(email="test@example.com", hashed_password="hashed_password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# Фікстура для створення тестового посту
@pytest.fixture
def test_post(db_session: Session, test_user):
    """
    Створюємо тестовий пост для використання в тестах коментарів.
    """
    post = Post(title="Test Post", content="Test Content", owner_id=test_user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post

# Фікстура для створення тестового коментаря
@pytest.fixture
def test_comment(db_session: Session, test_user, test_post):
    comment = Comment(content="Test Comment", post_id=test_post.id, owner_id=test_user.id)
    db_session.add(comment)
    db_session.commit()  # Фіксація змін
    db_session.refresh(comment)
    return comment


# Фікстура для створення даних коментаря
@pytest.fixture
def test_comment_data():
    return CommentCreate(content="Test comment content")

# Фікстура для сервісу CommentService
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





