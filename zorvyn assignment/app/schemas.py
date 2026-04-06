from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class RecordType(str, Enum):
    income = "income"
    expense = "expense"


class MessageResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    role: Role
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool
    created_at: str
    updated_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class FinancialRecordCreate(BaseModel):
    amount: float = Field(..., gt=0)
    type: RecordType
    category: str = Field(..., min_length=2, max_length=50)
    record_date: date
    description: Optional[str] = Field(default=None, max_length=500)


class FinancialRecordUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(default=None, min_length=2, max_length=50)
    record_date: Optional[date] = None
    description: Optional[str] = Field(default=None, max_length=500)


class FinancialRecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    record_date: date
    description: Optional[str] = None
    created_by: int
    created_by_username: str
    created_at: str
    updated_at: str


class CategoryTotal(BaseModel):
    type: RecordType
    category: str
    total: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expense: float
    net: float


class DashboardPeriod(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class DashboardTotals(BaseModel):
    income: float
    expenses: float
    net_balance: float


class DashboardSummaryResponse(BaseModel):
    period: DashboardPeriod
    totals: DashboardTotals
    category_totals: List[CategoryTotal]
    recent_activity: List[FinancialRecordResponse]
    monthly_trends: List[MonthlyTrend]
