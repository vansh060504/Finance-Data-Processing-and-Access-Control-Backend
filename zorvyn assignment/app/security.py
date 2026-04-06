from __future__ import annotations

import hashlib
import secrets
from typing import Dict, Optional

_TOKEN_STORE: Dict[str, int] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _TOKEN_STORE[token] = user_id
    return token


def get_user_id_for_token(token: str) -> Optional[int]:
    return _TOKEN_STORE.get(token)


def revoke_token(token: str) -> None:
    _TOKEN_STORE.pop(token, None)


def clear_tokens() -> None:
    _TOKEN_STORE.clear()
