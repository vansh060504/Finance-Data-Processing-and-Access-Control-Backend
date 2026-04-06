from __future__ import annotations

import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import crud, schemas
from app.dependencies import require_roles
from app.schemas import Role
from app.utils import convert_date_values, model_to_dict

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post(
    "",
    response_model=schemas.FinancialRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_record(
    payload: schemas.FinancialRecordCreate,
    current_user: dict = Depends(require_roles(Role.admin)),
) -> dict:
    try:
        record_data = convert_date_values(model_to_dict(payload))
        return crud.create_record(record_data, created_by=current_user["id"])
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create financial record due to invalid input.",
        )


@router.get("", response_model=list[schemas.FinancialRecordResponse])
def list_records(
    record_type: schemas.RecordType | None = Query(default=None, alias="type"),
    category: str | None = Query(default=None, min_length=2, max_length=50),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_roles(Role.analyst, Role.admin)),
) -> list[dict]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from cannot be greater than date_to.",
        )

    return crud.list_records(
        record_type=record_type.value if record_type else None,
        category=category,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=schemas.FinancialRecordResponse)
def get_record(
    record_id: int,
    _: dict = Depends(require_roles(Role.analyst, Role.admin)),
) -> dict:
    record = crud.get_record_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    return record


@router.patch("/{record_id}", response_model=schemas.FinancialRecordResponse)
def update_record(
    record_id: int,
    payload: schemas.FinancialRecordUpdate,
    _: dict = Depends(require_roles(Role.admin)),
) -> dict:
    updates = convert_date_values(model_to_dict(payload, exclude_unset=True))
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update.",
        )

    try:
        record = crud.update_record(record_id, updates)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update financial record due to invalid input.",
        )

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    return record


@router.delete("/{record_id}", response_model=schemas.MessageResponse)
def delete_record(
    record_id: int,
    _: dict = Depends(require_roles(Role.admin)),
) -> dict:
    deleted = crud.delete_record(record_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    return {"message": "Record deleted successfully."}
