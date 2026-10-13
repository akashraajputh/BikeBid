from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_buyer_bids_are_persisted_history_is_private_and_outbid_notification_is_saved():
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{suffix}@example.com",
                "username": f"bidder-{suffix}",
                "full_name": "Auction Flow Bidder",
                "password": "StrongPass123!",
            },
        )
        bidder_headers = {"Authorization": f"Bearer {registration.json()['token']}"}
        admin_headers = {
            "Authorization": "Bearer "
            + client.post(
                "/api/v1/auth/login",
                json={"email": "admin@bikebid.com", "password": "Admin123!"},
            ).json()["token"]
        }
        live_auctions = client.get("/api/v1/auctions/live")
        assert live_auctions.status_code == 200
        auction = live_auctions.json()[0]
        amount = max(
            auction["current_price"] + auction["minimum_increment"],
            auction["motorcycle"]["start_price"],
        )

        rejected = client.post(
            f"/api/v1/auctions/{auction['id']}/bids",
            headers=bidder_headers,
            json={"amount": amount - 0.01},
        )
        assert rejected.status_code == 400

        accepted = client.post(
            f"/api/v1/auctions/{auction['id']}/bids",
            headers=bidder_headers,
            json={"amount": amount},
        )
        assert accepted.status_code == 200
        assert accepted.json()["current_price"] == amount
        assert accepted.json()["bids"][0]["user_name"] == "Auction Flow Bidder"

        persisted = client.get(f"/api/v1/auctions/{auction['id']}/bids")
        assert persisted.status_code == 200
        assert persisted.json()[0]["amount"] == amount
        personal_bids = client.get("/api/v1/users/me/bids", headers=bidder_headers)
        assert personal_bids.status_code == 200
        assert any(item["auction_id"] == auction["id"] for item in personal_bids.json())
        assert client.get("/api/v1/users/me/bids").status_code == 401

        # Bid once more as a different user to check the prior high bidder is notified.
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "buyer@bikebid.com", "password": "Password123!"},
        )
        other_headers = {"Authorization": f"Bearer {login.json()['token']}"}
        outbid_amount = amount + auction["minimum_increment"]
        outbid = client.post(
            f"/api/v1/auctions/{auction['id']}/bids",
            headers=other_headers,
            json={"amount": outbid_amount},
        )
        assert outbid.status_code == 200
        notifications = client.get("/api/v1/notifications", headers=bidder_headers)
        assert notifications.status_code == 200
        assert any("outbid" in notification["title"].lower() for notification in notifications.json())
        assert client.get("/api/v1/admin/auctions", headers=admin_headers).status_code == 200
        assert client.get("/api/v1/admin/auctions", headers=other_headers).status_code == 403
