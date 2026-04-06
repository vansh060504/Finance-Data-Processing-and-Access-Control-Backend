from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.database import get_connection
from app.security import hash_password


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _to_user(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _to_record(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {
        "id": row["id"],
        "amount": float(row["amount"]),
        "type": row["type"],
        "category": row["category"],
        "record_date": row["record_date"],
        "description": row["description"],
        "created_by": row["created_by"],
        "created_by_username": row["created_by_username"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, full_name, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["username"].strip(),
                data["full_name"].strip(),
                hash_password(data["password"]),
                _enum_value(data["role"]),
                1 if data.get("is_active", True) else 0,
            ),
        )
        user_id = cursor.lastrowid
    return get_user_by_id(user_id)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, username, full_name, role, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    return _to_user(row)


def get_user_auth_data(username: str) -> Optional[Dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, username, full_name, password_hash, role, is_active, created_at, updated_at
            FROM users
            WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()
    if row is None:
        return None
    data = _to_user(row)
    data["password_hash"] = row["password_hash"]
    return data


def list_users() -> List[Dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, username, full_name, role, is_active, created_at, updated_at
            FROM users
            ORDER BY id ASC
            """
        ).fetchall()
    return [_to_user(row) for row in rows]


def update_user(user_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    set_clauses: List[str] = []
    parameters: List[Any] = []

    for key, value in updates.items():
        if key == "full_name":
            set_clauses.append("full_name = ?")
            parameters.append(str(value).strip())
        elif key == "password":
            set_clauses.append("password_hash = ?")
            parameters.append(hash_password(str(value)))
        elif key == "role":
            set_clauses.append("role = ?")
            parameters.append(_enum_value(value))
        elif key == "is_active":
            set_clauses.append("is_active = ?")
            parameters.append(1 if bool(value) else 0)

    if not set_clauses:
        return get_user_by_id(user_id)

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    parameters.append(user_id)

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE users
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """,
            tuple(parameters),
        )
        if cursor.rowcount == 0:
            return None
    return get_user_by_id(user_id)


def delete_user(user_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cursor.rowcount > 0


def count_active_admins(excluding_user_id: Optional[int] = None) -> int:
    query = "SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND is_active = 1"
    params: List[Any] = []
    if excluding_user_id is not None:
        query += " AND id != ?"
        params.append(excluding_user_id)

    with get_connection() as connection:
        row = connection.execute(query, tuple(params)).fetchone()
    return int(row["count"])


def create_record(data: Dict[str, Any], created_by: int) -> Dict[str, Any]:
    record_date = data["record_date"]
    if hasattr(record_date, "isoformat"):
        record_date = record_date.isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO financial_records (amount, type, category, record_date, description, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                float(data["amount"]),
                _enum_value(data["type"]),
                data["category"].strip(),
                record_date,
                data.get("description"),
                created_by,
            ),
        )
        record_id = cursor.lastrowid

    return get_record_by_id(record_id)


def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                fr.id,
                fr.amount,
                fr.type,
                fr.category,
                fr.record_date,
                fr.description,
                fr.created_by,
                u.username AS created_by_username,
                fr.created_at,
                fr.updated_at
            FROM financial_records fr
            INNER JOIN users u ON u.id = fr.created_by
            WHERE fr.id = ?
            """,
            (record_id,),
        ).fetchone()
    return _to_record(row)


def list_records(
    *,
    record_type: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    where_clauses: List[str] = []
    params: List[Any] = []

    if record_type:
        where_clauses.append("fr.type = ?")
        params.append(_enum_value(record_type))
    if category:
        where_clauses.append("fr.category = ?")
        params.append(category.strip())
    if date_from:
        where_clauses.append("fr.record_date >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("fr.record_date <= ?")
        params.append(date_to)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    params.extend([limit, offset])

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
                fr.id,
                fr.amount,
                fr.type,
                fr.category,
                fr.record_date,
                fr.description,
                fr.created_by,
                u.username AS created_by_username,
                fr.created_at,
                fr.updated_at
            FROM financial_records fr
            INNER JOIN users u ON u.id = fr.created_by
            {where_sql}
            ORDER BY fr.record_date DESC, fr.id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params),
        ).fetchall()
    return [_to_record(row) for row in rows]


def update_record(record_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    set_clauses: List[str] = []
    params: List[Any] = []

    for key, value in updates.items():
        if key == "amount":
            set_clauses.append("amount = ?")
            params.append(float(value))
        elif key == "type":
            set_clauses.append("type = ?")
            params.append(_enum_value(value))
        elif key == "category":
            set_clauses.append("category = ?")
            params.append(str(value).strip())
        elif key == "record_date":
            date_value = value.isoformat() if hasattr(value, "isoformat") else str(value)
            set_clauses.append("record_date = ?")
            params.append(date_value)
        elif key == "description":
            set_clauses.append("description = ?")
            params.append(value)

    if not set_clauses:
        return get_record_by_id(record_id)

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.append(record_id)

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE financial_records
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """,
            tuple(params),
        )
        if cursor.rowcount == 0:
            return None
    return get_record_by_id(record_id)


def delete_record(record_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM financial_records WHERE id = ?", (record_id,))
    return cursor.rowcount > 0


def get_dashboard_summary(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    where_clauses: List[str] = []
    params: List[Any] = []

    if date_from:
        where_clauses.append("fr.record_date >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("fr.record_date <= ?")
        params.append(date_to)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with get_connection() as connection:
        totals = connection.execute(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN fr.type = 'income' THEN fr.amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN fr.type = 'expense' THEN fr.amount ELSE 0 END), 0) AS total_expense
            FROM financial_records fr
            {where_sql}
            """,
            tuple(params),
        ).fetchone()

        category_rows = connection.execute(
            f"""
            SELECT fr.type, fr.category, ROUND(SUM(fr.amount), 2) AS total
            FROM financial_records fr
            {where_sql}
            GROUP BY fr.type, fr.category
            ORDER BY total DESC
            """,
            tuple(params),
        ).fetchall()

        recent_rows = connection.execute(
            f"""
            SELECT
                fr.id,
                fr.amount,
                fr.type,
                fr.category,
                fr.record_date,
                fr.description,
                fr.created_by,
                u.username AS created_by_username,
                fr.created_at,
                fr.updated_at
            FROM financial_records fr
            INNER JOIN users u ON u.id = fr.created_by
            {where_sql}
            ORDER BY fr.record_date DESC, fr.id DESC
            LIMIT 5
            """,
            tuple(params),
        ).fetchall()

        monthly_rows = connection.execute(
            f"""
            SELECT
                SUBSTR(fr.record_date, 1, 7) AS month,
                COALESCE(SUM(CASE WHEN fr.type = 'income' THEN fr.amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN fr.type = 'expense' THEN fr.amount ELSE 0 END), 0) AS expense
            FROM financial_records fr
            {where_sql}
            GROUP BY SUBSTR(fr.record_date, 1, 7)
            ORDER BY month ASC
            """,
            tuple(params),
        ).fetchall()

    total_income = float(totals["total_income"])
    total_expense = float(totals["total_expense"])

    return {
        "period": {
            "date_from": date_from,
            "date_to": date_to,
        },
        "totals": {
            "income": round(total_income, 2),
            "expenses": round(total_expense, 2),
            "net_balance": round(total_income - total_expense, 2),
        },
        "category_totals": [
            {
                "type": row["type"],
                "category": row["category"],
                "total": float(row["total"]),
            }
            for row in category_rows
        ],
        "recent_activity": [_to_record(row) for row in recent_rows],
        "monthly_trends": [
            {
                "month": row["month"],
                "income": round(float(row["income"]), 2),
                "expense": round(float(row["expense"]), 2),
                "net": round(float(row["income"]) - float(row["expense"]), 2),
            }
            for row in monthly_rows
        ],
    }
