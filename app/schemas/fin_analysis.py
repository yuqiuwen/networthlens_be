from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer, field_validator


AnalysisGranularity = Literal["week", "month", "year"]
TransactionRankType = Literal["income", "expense"]
TransactionRankOrder = Literal["asc", "desc"]
TransactionRankTimeRange = Literal["this_week", "this_month", "this_year"]


# =====================
# Query
# =====================


class BaseAnalysisQuery(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def remove_timezone(cls, value: datetime | None):
        if value is None:
            return None

        return value.replace(tzinfo=None)


class ExpenseAnalysisQuery(BaseAnalysisQuery):
    category_ids: list[str] | None = None
    source_account_ids: list[str] | None = None
    target_account_ids: list[str] | None = None
    granularity: AnalysisGranularity = "month"
    period_count: int | None = Field(default=None, ge=1, le=120)


class TransactionRankQuery(BaseAnalysisQuery):
    transaction_type: TransactionRankType = "expense"
    sort_order: TransactionRankOrder = "desc"
    limit: int = Field(default=10, ge=1, le=100)
    currency: str = Field(default="CNY", min_length=3, max_length=3)
    time_range: TransactionRankTimeRange | None = None
    include_refunded: bool = False

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class AssetAnalysisQuery(BaseAnalysisQuery):
    asset_types: list[int] | None = None


class GoalAnalysisQuery(BaseAnalysisQuery):
    goal_ids: list[str] | None = None


class LiabilityAnalysisQuery(BaseAnalysisQuery):
    liability_types: list[int] | None = None


# =====================
# Result
# =====================


class NetWorthAnalysisResult(BaseModel):
    total_asset: int
    total_liability: int
    net_worth: int

    @field_serializer("total_asset", "net_worth")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class ExpenseCategoryItem(BaseModel):
    category_id: str | None
    category_name: str | None
    amount: int
    ratio: float

    @field_serializer("amount")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class ExpenseTrendItem(BaseModel):
    period: str
    income: int
    expense: int
    balance: int

    @field_serializer("income", "expense", "balance")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class ExpenseAnalysisResult(BaseModel):
    income: int
    expense: int
    balance: int
    top_categories: list[ExpenseCategoryItem]
    granularity: AnalysisGranularity = "month"
    trend: list[ExpenseTrendItem] = Field(default_factory=list)

    @field_serializer("income", "expense", "balance")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class TransactionRankItem(BaseModel):
    rank: int
    category_id: str | None
    category_name: str | None
    amount: int
    currency: str
    merchant: str | None
    product: str | None
    occurred_at: datetime
    status: str

    @field_serializer("amount")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class TransactionRankResult(BaseModel):
    transaction_type: TransactionRankType
    sort_order: TransactionRankOrder
    currency: str
    include_refunded: bool = False
    start_time: datetime | None
    end_time: datetime | None
    items: list[TransactionRankItem]


class AssetAllocationItem(BaseModel):
    asset_type: int
    asset_name: str
    amount: int
    ratio: float

    @field_serializer("amount")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")
        

class AssetAnalysisResult(BaseModel):
    total_asset: int
    allocations: list[AssetAllocationItem]

    @field_serializer("total_asset")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class LiabilityAnalysisResult(BaseModel):
    total_liability: int
    active_count: int
    settled_count: int


    @field_serializer("total_liability")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class GoalForecastItem(BaseModel):
    goal_id: str
    goal_name: str
    target_amount: int
    current_amount: int
    remaining_amount: int
    estimated_months: int | None

    @field_serializer("target_amount", "current_amount", "remaining_amount")
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")


class GoalAnalysisResult(BaseModel):
    goals: list[GoalForecastItem]


class FinancialSnapshotResult(BaseModel):
    total_asset: int
    total_liability: int
    net_worth: int
    asset_count: int
    liability_count: int

    @field_serializer(
        "total_asset",
        "total_liability",
        "net_worth",
    )
    def serialize_amount(self, value: int) -> Decimal:
        return Decimal(value) / Decimal("100")
