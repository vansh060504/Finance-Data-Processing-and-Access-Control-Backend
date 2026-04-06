from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, status

from app import crud
from app.schemas import Role
from app.security import get_user_id_for_token


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required.",
        )

    parts = authorization.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer token format.",
        )

    token = parts[1].strip()
    user_id = get_user_id_for_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    user = crud.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User for token was not found.",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    user["token"] = token
    return user


def require_roles(*allowed_roles: Role | str) -> Callable[..., dict[str, Any]]:
    allowed = {role.value if isinstance(role, Role) else str(role) for role in allowed_roles}

    def role_guard(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user["role"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user['role']}' is not allowed for this action.",
            )
        return current_user

    return role_guard
