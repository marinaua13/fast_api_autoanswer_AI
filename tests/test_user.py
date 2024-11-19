from fastapi.testclient import TestClient

# Використовуємо фікстуру `client` з `conftest.py`
def test_register_user(client: TestClient):
    response = client.post(
        "/users/",
        json={"email": "testuser@example.com", "password": "password123"}
    )
    assert response.status_code == 201

def test_login_user(client: TestClient):
    # Спочатку реєструємо користувача
    client.post(
        "/users/",
        json={"email": "testuser@example.com", "password": "password123"}
    )
    # Тестуємо логін користувача
    response = client.post(
        "/users/login",
        json={"email": "testuser@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


# Тест логіну з неправильним паролем
def test_login_user_wrong_password(client: TestClient):
    """Тест логіну користувача з неправильним паролем"""
    login_response = client.post(
        "/users/login",
        json={"email": "loginuser@example.com", "password": "wrongpassword"}
    )
    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Invalid credentials"}
