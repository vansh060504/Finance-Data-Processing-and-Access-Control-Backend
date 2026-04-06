from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app import crud, schemas
from app.dependencies import get_current_user
from app.security import issue_token, revoke_token, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest) -> dict:
    user_auth = crud.get_user_auth_data(payload.username)
    if user_auth is None or not verify_password(payload.password, user_auth["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    if not user_auth["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    token = issue_token(user_auth["id"])
    user = crud.get_user_by_id(user_auth["id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout", response_model=schemas.MessageResponse)
def logout(current_user: dict = Depends(get_current_user)) -> dict:
    token = current_user.get("token")
    if token:
        revoke_token(token)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
