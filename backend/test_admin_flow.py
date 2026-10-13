from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_admin_creates_and_schedules_motorcycle_auction_and_buyer_is_denied():
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        admin_login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bikebid.com", "password": "Admin123!"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['token']}"}
        buyer_login = client.post(
            "/api/v1/auth/login",
            json={"email": "buyer@bikebid.com", "password": "Password123!"},
        )
        buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['token']}"}

        assert client.get("/api/v1/admin/summary", headers=admin_headers).status_code == 200
        assert client.get("/api/v1/admin/analytics", headers=admin_headers).status_code == 200

        motorcycle = client.post(
            "/api/v1/admin/motorcycles",
            headers=admin_headers,
            json={
                "title": f"Flow Motorcycle {suffix}",
                "description": "Listing created for the admin workflow.",
                "manufacturer": "Example",
                "model": "Flow 500",
                "year": 2024,
                "mileage": 50,
                "engine_cc": 500,
                "fuel_type": "Petrol",
                "condition": "Excellent",
                "location": "Bengaluru",
                "start_price": "1000.00",
                "reserve_price": "1200.00",
                "image_urls": [],
            },
        )
        assert motorcycle.status_code == 201
        motorcycle_id = motorcycle.json()["id"]
        edited = client.patch(
            f"/api/v1/admin/motorcycles/{motorcycle_id}",
            headers=admin_headers,
            json={"start_price": "1100.00"},
        )
        assert edited.status_code == 200
        assert edited.json()["start_price"] == 1100

        now = datetime.now(timezone.utc)
        auction = client.post(
            "/api/v1/admin/auctions",
            headers=admin_headers,
            json={
                "motorcycle_id": motorcycle_id,
                "start_time": (now + timedelta(hours=1)).isoformat(),
                "end_time": (now + timedelta(hours=2)).isoformat(),
                "minimum_increment": "25.00",
            },
        )
        assert auction.status_code == 201
        auction_id = auction.json()["id"]
        scheduled = client.post(
            f"/api/v1/admin/auctions/{auction_id}/schedule",
            headers=admin_headers,
        )
        assert scheduled.status_code == 200
        assert scheduled.json()["status"] == "SCHEDULED"

        assert client.get("/api/v1/admin/analytics", headers=buyer_headers).status_code == 403
        assert client.get("/api/v1/admin/motorcycles", headers=buyer_headers).status_code == 403
        assert client.get(f"/api/v1/admin/auctions/{auction_id}").status_code == 401
