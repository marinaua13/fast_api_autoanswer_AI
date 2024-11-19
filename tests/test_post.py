from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from models import Post, User
from modules.post import crud, schemas
from core.auth import create_access_token


def test_create_post_crud(db_session: Session, test_user):
    # Перевірка створення поста через CRUD
    post_data = schemas.PostCreate(title="Test Title", content="Test Content")
    post = crud.create_post(db=db_session, post=post_data, user_id=test_user.id)

    assert post.id is not None
    assert post.title == "Test Title"
    assert post.content == "Test Content"
    assert post.owner_id == test_user.id


def test_create_post_route(client: TestClient, db_session: Session, test_user: User):
    # Згенеруємо токен для test_user
    access_token = create_access_token({"sub": test_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}

    # Тест створення поста через API маршрут
    response = client.post(
        "/posts/",
        json={"title": "Test Title", "content": "Test Content"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Title"
    assert data["content"] == "Test Content"

def test_read_post_route(client: TestClient, db_session: Session, test_user):
    # Тест читання поста через API маршрут
    post = Post(title="Test Title", content="Test Content", owner_id=test_user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    response = client.get(f"/posts/{post.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Title"
    assert data["content"] == "Test Content"
