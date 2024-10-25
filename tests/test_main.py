import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models import Base, Comment
from dependencies import get_db
from datetime import datetime, timedelta
from jose import jwt


# test data
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# secret_key and algor. for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def test_user(client):
    user_data = {"email": "testuser@example.com", "username": "testuser", "password": "password"}
    client.post("/users/", json=user_data)
    return user_data


@pytest.fixture(scope="module")
def token(client, test_user):
    response = client.post("/token", data={"username": test_user["email"], "password": test_user["password"]})
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def authorized_client(client, token):
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_create_user(client):
    response = client.post("/users/", json={"email": "newuser@example.com", "username": "newuser", "password": "password"})
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"
    assert response.json()["username"] == "newuser"


def test_login_user(client, test_user):
    response = client.post("/token", data={"username": test_user["email"], "password": test_user["password"]})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_create_post(authorized_client):
    response = authorized_client.post("/posts/", json={"title": "Test Post", "content": "This is a clean post."})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["content"] == "This is a clean post."
    assert data["title"] == "Test Post"


def test_create_comment(authorized_client, test_user, client):
    post_response = authorized_client.post("/posts/", json={"title": "Test Post", "content": "This is a clean post."})
    assert post_response.status_code == 200
    post_data = post_response.json()
    post_id = post_data["id"]

    comment_response = authorized_client.post("/comments/", json={"content": "This is a comment.", "post_id": post_id})
    assert comment_response.status_code == 200
    comment_data = comment_response.json()
    assert "id" in comment_data
    assert comment_data["post_id"] == post_id
    assert "content" in comment_data

    assert comment_data["content"] is not None


def test_comments_breakdown(authorized_client, test_db):
    # Create a post
    post_response = authorized_client.post("/posts/",
                                           json={"title": "Analytics Post", "content": "Post for analytics."})
    assert post_response.status_code == 200
    post_data = post_response.json()
    post_id = post_data["id"]

    # Create comments for the post, explicitly setting is_blocked
    comment_data = [
        {"content": "Comment 1", "post_id": post_id, "is_blocked": False},
        {"content": "Comment 2", "post_id": post_id, "is_blocked": True},
        {"content": "Comment 3", "post_id": post_id, "is_blocked": False},
        {"content": "Comment 4", "post_id": post_id, "is_blocked": True},
    ]
    created_comments = []
    for comment in comment_data:
        response = authorized_client.post("/comments/", json=comment)
        assert response.status_code == 200
        created_comments.append(response.json())

    # Update the created_at field directly in the database to simulate different days
    date_1 = datetime.strptime("2024-10-01T10:00:00", "%Y-%m-%dT%H:%M:%S")
    date_2 = date_1 + timedelta(days=1)

    test_db.query(Comment).filter_by(id=created_comments[0]['id']).update({"created_at": date_1, "is_blocked": False})
    test_db.query(Comment).filter_by(id=created_comments[1]['id']).update({"created_at": date_1, "is_blocked": True})
    test_db.query(Comment).filter_by(id=created_comments[2]['id']).update({"created_at": date_2, "is_blocked": False})
    test_db.query(Comment).filter_by(id=created_comments[3]['id']).update({"created_at": date_2, "is_blocked": True})
    test_db.commit()

    # Call the analytics endpoint and check the breakdown
    date_from = "2024-10-01"
    date_to = "2024-10-03"
    response = authorized_client.get(f"/comments-daily-breakdown/?date_from={date_from}&date_to={date_to}")
    assert response.status_code == 200

    # Check if the breakdown has the correct data
    breakdown_data = response.json()
    print(f"Analytics Data: {breakdown_data}")

    # Check for 2024-10-01
    assert len(breakdown_data) > 0
    assert breakdown_data[0]["date"] == "2024-10-01"
    assert breakdown_data[0]["total_comments"] == 2
    assert breakdown_data[0]["blocked_comments"] == 1

    # Check for 2024-10-02
    assert len(breakdown_data) > 1
    assert breakdown_data[1]["date"] == "2024-10-02"
    assert breakdown_data[1]["total_comments"] == 2
    assert breakdown_data[1]["blocked_comments"] == 1
