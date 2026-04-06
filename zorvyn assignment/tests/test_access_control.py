from __future__ import annotations


def login(client, username: str, password: str) -> dict:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_viewer_and_analyst_access_restrictions(client) -> None:
    admin_headers = login(client, "admin", "admin123")

    viewer_response = client.post(
        "/users",
        json={
            "username": "viewer_user",
            "full_name": "Viewer User",
            "password": "viewerpass",
            "role": "viewer",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert viewer_response.status_code == 201, viewer_response.text

    analyst_response = client.post(
        "/users",
        json={
            "username": "analyst_user",
            "full_name": "Analyst User",
            "password": "analystpass",
            "role": "analyst",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert analyst_response.status_code == 201, analyst_response.text

    viewer_headers = login(client, "viewer_user", "viewerpass")
    analyst_headers = login(client, "analyst_user", "analystpass")

    payload = {
        "amount": 1000,
        "type": "income",
        "category": "Salary",
        "record_date": "2026-01-10",
        "description": "January salary",
    }

    viewer_create = client.post("/records", json=payload, headers=viewer_headers)
    assert viewer_create.status_code == 403

    viewer_list = client.get("/records", headers=viewer_headers)
    assert viewer_list.status_code == 403

    viewer_summary = client.get("/dashboard/summary", headers=viewer_headers)
    assert viewer_summary.status_code == 200, viewer_summary.text

    analyst_create = client.post("/records", json=payload, headers=analyst_headers)
    assert analyst_create.status_code == 403

    analyst_list = client.get("/records", headers=analyst_headers)
    assert analyst_list.status_code == 200, analyst_list.text


def test_inactive_user_cannot_login(client) -> None:
    admin_headers = login(client, "admin", "admin123")

    create_response = client.post(
        "/users",
        json={
            "username": "inactive_user",
            "full_name": "Inactive User",
            "password": "inactivepass",
            "role": "viewer",
            "is_active": False,
        },
        headers=admin_headers,
    )
    assert create_response.status_code == 201, create_response.text

    login_response = client.post(
        "/auth/login",
        json={"username": "inactive_user", "password": "inactivepass"},
    )
    assert login_response.status_code == 403
