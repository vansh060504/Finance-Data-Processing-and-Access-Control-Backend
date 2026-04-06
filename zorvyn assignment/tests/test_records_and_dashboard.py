from __future__ import annotations

import pytest


def login(client, username: str, password: str) -> dict:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_record_filters_and_dashboard_summary(client) -> None:
    admin_headers = login(client, "admin", "admin123")

    analyst_user = client.post(
        "/users",
        json={
            "username": "finance_analyst",
            "full_name": "Finance Analyst",
            "password": "analystpass",
            "role": "analyst",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert analyst_user.status_code == 201, analyst_user.text
    analyst_headers = login(client, "finance_analyst", "analystpass")

    records = [
        {
            "amount": 5000,
            "type": "income",
            "category": "Salary",
            "record_date": "2026-01-05",
            "description": "Monthly salary",
        },
        {
            "amount": 1500,
            "type": "expense",
            "category": "Rent",
            "record_date": "2026-01-06",
            "description": "House rent",
        },
        {
            "amount": 300,
            "type": "expense",
            "category": "Food",
            "record_date": "2026-01-10",
            "description": "Groceries",
        },
        {
            "amount": 1200,
            "type": "income",
            "category": "Freelance",
            "record_date": "2026-02-01",
            "description": "Side project",
        },
    ]

    for record in records:
        create_response = client.post("/records", json=record, headers=admin_headers)
        assert create_response.status_code == 201, create_response.text

    january_expenses = client.get(
        "/records?type=expense&date_from=2026-01-01&date_to=2026-01-31",
        headers=analyst_headers,
    )
    assert january_expenses.status_code == 200, january_expenses.text
    january_expense_items = january_expenses.json()
    assert len(january_expense_items) == 2

    food_only = client.get(
        "/records?category=Food",
        headers=analyst_headers,
    )
    assert food_only.status_code == 200, food_only.text
    food_items = food_only.json()
    assert len(food_items) == 1
    assert food_items[0]["category"] == "Food"

    january_summary = client.get(
        "/dashboard/summary?date_from=2026-01-01&date_to=2026-01-31",
        headers=analyst_headers,
    )
    assert january_summary.status_code == 200, january_summary.text
    january_data = january_summary.json()
    assert january_data["totals"]["income"] == pytest.approx(5000.0)
    assert january_data["totals"]["expenses"] == pytest.approx(1800.0)
    assert january_data["totals"]["net_balance"] == pytest.approx(3200.0)
    assert len(january_data["monthly_trends"]) == 1
    assert january_data["monthly_trends"][0]["month"] == "2026-01"

    full_summary = client.get("/dashboard/summary", headers=analyst_headers)
    assert full_summary.status_code == 200, full_summary.text
    full_data = full_summary.json()
    assert full_data["totals"]["income"] == pytest.approx(6200.0)
    assert full_data["totals"]["expenses"] == pytest.approx(1800.0)
    assert full_data["totals"]["net_balance"] == pytest.approx(4400.0)
    assert len(full_data["monthly_trends"]) == 2
    assert full_data["recent_activity"][0]["record_date"] == "2026-02-01"
