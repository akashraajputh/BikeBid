from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_register_refresh_logout_and_reject_revoked_session():
    suffix = uuid4().hex[:12]
    with TestClient(app) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{suffix}@example.com",
                "username": f"buyer-{suffix}",
                "full_name": "Flow Test Buyer",
                "password": "StrongPass123!",
                "role": "admin",
            },
        )
        assert registration.status_code == 200
        auth = registration.json()
        assert auth["user"]["role"] == "buyer"

        login = client.post(
            "/api/v1/auth/login",
            json={"email": f"{suffix}@example.com", "password": "StrongPass123!"},
        )
        assert login.status_code == 200
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/auth/me", headers=headers).json()["email"] == f"{suffix}@example.com"

        refreshed = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth["refresh_token"]},
        )
        assert refreshed.status_code == 200
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
        assert client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refreshed.json()['token']}"},
        ).status_code == 401
