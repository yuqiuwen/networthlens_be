from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.schemas.category import CategorySchema
from pydantic import BaseModel, Field

from app.schemas.common import EntityModel
from app.constant import TransactionChannel, TransactionStatus, TransactionType



class CreateTransactionSchema(BaseModel):
    channel: TransactionChannel = TransactionChannel.OTHER

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
    start_time: datetime | None = None
    end_time: datetime | None = None


class TransactionListSchema(EntityModel):
    id: str
    channel: TransactionChannel | None
    transaction_type: TransactionType
    category_id: str | None
    source_account_id: str | None
    target_account_id: str | None
    amount: int
    currency: str
    merchant: str | None
    product: str | None
    note: str | None
    occurred_at: datetime
    status: TransactionStatus

    category: CategorySchema | None = None


class TransactionDetailSchema(EntityModel):
    id: str
    channel: TransactionChannel | None
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
    import_source: Literal["wx", "alipay"]


class TransactionSummarySchema(BaseModel):
    income: int = 0
    expense: int = 0
    balance: int = 0
