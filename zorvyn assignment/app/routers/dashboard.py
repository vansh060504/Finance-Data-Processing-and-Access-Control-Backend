from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import crud, schemas
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummaryResponse)
def get_dashboard_summary(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: dict = Depends(get_current_user),
) -> dict:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from cannot be greater than date_to.",
        )

    return crud.get_dashboard_summary(
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
    )
