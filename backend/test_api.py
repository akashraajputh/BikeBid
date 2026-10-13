from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck():
    with TestClient(app) as client:
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'


def test_register_and_login():
    with TestClient(app) as client:
        suffix = uuid4().hex[:10]
        payload = {
            'email': f'{suffix}@example.com',
            'username': f'user-{suffix}',
            'full_name': 'New User',
            'password': 'StrongPass123!'
        }
        register = client.post('/api/auth/register', json=payload)
        assert register.status_code == 200
        token = register.json()['token']
        assert token

        login = client.post('/api/auth/login', json={'email': payload['email'], 'password': 'StrongPass123!'})
        assert login.status_code == 200
        assert login.json()['user']['email'] == payload['email']


def test_list_motorcycles():
    with TestClient(app) as client:
        response = client.get('/api/motorcycles')
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 1


def test_auction_and_dashboard_routes():
    with TestClient(app) as client:
        auctions = client.get('/api/auctions')
        assert auctions.status_code == 200
        live_auction = next(item for item in auctions.json() if item['status'] == 'LIVE')

        login = client.post(
            '/api/auth/login',
            json={'email': 'buyer@bikebid.com', 'password': 'Password123!'},
        )
        assert login.status_code == 200
        token = login.json()['token']
        headers = {'Authorization': f'Bearer {token}'}

        bid_response = client.post(
            f"/api/auctions/{live_auction['id']}/bid",
            headers=headers,
            json={'amount': live_auction['current_price'] + live_auction['minimum_increment']},
        )
        assert bid_response.status_code == 200
        assert bid_response.json()['bids'][0]['amount'] == live_auction['current_price'] + live_auction['minimum_increment']

        dashboard = client.get('/api/dashboard', headers=headers)
        assert dashboard.status_code == 200
        assert len(dashboard.json()['recent_bids']) >= 1


def test_admin_summary_requires_admin():
    with TestClient(app) as client:
        login = client.post(
            '/api/auth/login',
            json={'email': 'admin@bikebid.com', 'password': 'Admin123!'},
        )
        assert login.status_code == 200
        response = client.get(
            '/api/admin/summary',
            headers={'Authorization': f"Bearer {login.json()['token']}"},
        )
        assert response.status_code == 200
        assert response.json()['auctions'] >= 1


def test_admin_can_create_and_schedule_auction():
    with TestClient(app) as client:
        login = client.post(
            '/api/auth/login',
            json={'email': 'admin@bikebid.com', 'password': 'Admin123!'},
        )
        headers = {'Authorization': f"Bearer {login.json()['token']}"}
        motorcycle = client.post(
            '/api/motorcycles',
            headers=headers,
            json={
                'title': 'Integration Test Bike',
                'description': 'Created by the API integration test.',
                'manufacturer': 'Test',
                'model': 'Test 500',
                'year': 2024,
                'mileage': 100,
                'engine_cc': 500,
                'fuel_type': 'Petrol',
                'condition': 'Good',
                'location': 'Bengaluru',
                'start_price': '1000.00',
                'reserve_price': '1200.00',
                'image_urls': [],
            },
        )
        assert motorcycle.status_code == 201

        now = datetime.now(timezone.utc)
        auction = client.post(
            '/api/auctions',
            headers=headers,
            json={
                'motorcycle_id': motorcycle.json()['id'],
                'start_time': (now + timedelta(hours=1)).isoformat(),
                'end_time': (now + timedelta(hours=2)).isoformat(),
            },
        )
        assert auction.status_code == 201
        auction_id = auction.json()['id']

        published = client.post(f'/api/auctions/{auction_id}/publish', headers=headers)
        assert published.status_code == 200
        assert published.json()['status'] == 'SCHEDULED'
