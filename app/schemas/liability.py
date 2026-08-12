from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import EntityModel
from app.constant import (
    LiabilityStatus,
    LiabilityType,
    RepaymentType,
)


class CreateLiabilitySchema(BaseModel):
    liability_type: LiabilityType
    name: str

    original_principal: int
    remaining_principal: int

    interest_rate: float = 0

    repayment_type: RepaymentType

    monthly_payment: int | None = None

    currency: str = "CNY"

    start_date: date | None = None
    due_date: date | None = None

    note: str | None = None


class UpdateLiabilitySchema(BaseModel):
    name: str | None = None

    interest_rate: float | None = None

    repayment_type: RepaymentType | None = None

    monthly_payment: int | None = None

    due_date: date | None = None

    status: LiabilityStatus | None = None

    note: str | None = None


class LiabilityQuerySchema(BaseModel):
    page: int = 1
    limit: int = 20

    liability_type: LiabilityType | None = None
    status: LiabilityStatus | None = None


class LiabilityListSchema(BaseModel):
    id: str
    name: str

    liability_type: LiabilityType

    original_principal: int
    remaining_principal: int

    status: LiabilityStatus


class LiabilityDetailSchema(BaseModel):
    id: str

    liability_type: LiabilityType

    name: str

    original_principal: int
    remaining_principal: int

    interest_rate: float

    repayment_type: RepaymentType

    monthly_payment: int | None

    currency: str

    start_date: date | None
    due_date: date | None

    status: LiabilityStatus

    note: str | None



class CreateRepaymentSchema(BaseModel):
    transaction_id: str | None = None

    repayment_amount: int

    principal: int

    interest: int = 0

    fee: int = 0

    note: str | None = None


class RepaymentSchema(BaseModel):
    id: str

    repayment_amount: int

    principal: int

    interest: int

    fee: int

    remaining_principal: int

    paid_at: datetime

    note: str | None
