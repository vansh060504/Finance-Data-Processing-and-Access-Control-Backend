from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app import crud, schemas
from app.dependencies import require_roles
from app.schemas import Role
from app.utils import model_to_dict

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: schemas.UserCreate,
    _: dict = Depends(require_roles(Role.admin)),
) -> dict:
    try:
        return crud.create_user(model_to_dict(payload))
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )


@router.get("", response_model=list[schemas.UserResponse])
def list_users(_: dict = Depends(require_roles(Role.admin))) -> list[dict]:
    return crud.list_users()


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, _: dict = Depends(require_roles(Role.admin))) -> dict:
    user = crud.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.patch("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    current_user: dict = Depends(require_roles(Role.admin)),
) -> dict:
    existing_user = crud.get_user_by_id(user_id)
    if existing_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    updates = model_to_dict(payload, exclude_unset=True, exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update.",
        )

    if (
        existing_user["role"] == Role.admin.value
        and existing_user["is_active"]
        and (
            updates.get("role", existing_user["role"]) != Role.admin.value
            or updates.get("is_active", existing_user["is_active"]) is False
        )
        and crud.count_active_admins(excluding_user_id=user_id) == 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one active admin must remain in the system.",
        )

    if current_user["id"] == user_id and updates.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    try:
        updated_user = crud.update_user(user_id, updates)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not update user due to a uniqueness conflict.",
        )

    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return updated_user


@router.delete("/{user_id}", response_model=schemas.MessageResponse)
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_roles(Role.admin)),
) -> dict:
    user = crud.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )

    if (
        user["role"] == Role.admin.value
        and user["is_active"]
        and crud.count_active_admins(excluding_user_id=user_id) == 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one active admin must remain in the system.",
        )

    deleted = crud.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return {"message": "User deleted successfully."}
