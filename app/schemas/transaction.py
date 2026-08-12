from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import EntityModel
from app.constant import TransactionStatus, TransactionType



class CreateTransactionSchema(BaseModel):
    transaction_type: TransactionType

    category_id: str | None = None

    source_account_id: str | None = None
    target_account_id: str | None = None

    amount: int = Field(gt=0)

    currency: str = "CNY"

    merchant: str | None = None

    product: str | None = None

    occurred_at: datetime

    note: str | None = None

    transaction_id: str | None = None


class UpdateTransactionSchema(BaseModel):
    category_id: str | None = None
    merchant: str | None = None
    product: str | None = None
    note: str | None = None
    status: TransactionStatus | None = None


class TransactionQuerySchema(BaseModel):
    page: int = 1
    limit: int = 20

    transaction_type: TransactionType | None = None
    category_id: str | None = None
    source_account_id: str | None = None
    target_account_id: str | None = None
    start_time: datetime
    end_time: datetime


class TransactionListSchema(BaseModel):
    id: str
    transaction_type: TransactionType
    amount: int
    currency: str
    merchant: str | None
    occurred_at: datetime
    status: TransactionStatus


class TransactionDetailSchema(EntityModel):
    id: str
    transaction_id: str | None
    transaction_type: TransactionType
    category_id: str | None
    source_account_id: str | None
    target_account_id: str | None
    amount: int
    currency: str
    merchant: str | None
    product: str | None
    occurred_at: datetime
    note: str | None
    status: TransactionStatus


class ImportTransactionSchema(BaseModel):
    success_count: int
    failed_count: int