from dataclasses import dataclass
from enum import StrEnum
from datetime import date
from decimal import Decimal
import hashlib
import json
from dateutil.relativedelta import relativedelta


from app.constant import AccountType, InsightLevel, InsightType
from pydantic import BaseModel, Field, field_serializer, field_validator, computed_field


"""
第一屏
总资产 | 可用资金 | 本月收入 | 本月支出 | 本月结余

第二屏
收支趋势                 消费分类

第三屏
资金账户                 个人资产
招商 ¥82k                房产 ¥200w
工行 ¥43k                汽车 ¥25w
支付宝 ¥21k              黄金 ¥12w

第四屏
个人财富趋势

第五屏
AI 财务洞察

"""


@dataclass(frozen=True)
class DateRange:
    start_date: date
    end_date: date



class DashboardPeriod(StrEnum):
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"



class TrendGranularity(StrEnum):
    DAY = "day"
    MONTH = "month"
    

def get_trend_granularity(period: DashboardPeriod) -> str:
    if period == DashboardPeriod.MONTH:
        return "day"
    if period == DashboardPeriod.QUARTER:
        return "month"
    if period == DashboardPeriod.YEAR:
        return "month"
    raise ValueError("Unsupported period")
    

class DashboardQuery(BaseModel):
    period: DashboardPeriod = DashboardPeriod.MONTH

    # 不传默认 today
    query_date: date | None = None

    # 趋势图数据粒度，自动判断
    # granularity: TrendGranularity = TrendGranularity.DAY

    start_date: date | None = None
    end_date: date | None = None 


    def to_cache_key(self) -> str:
        data = self.model_dump(exclude_unset=True, exclude_none=True)
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()

    @computed_field
    @property
    def granularity(self) -> str:
        return get_trend_granularity(self.period)



class DashboardMetrics(BaseModel):
    # 资金账户余额之和
    available_funds: Decimal = 0

    # 非资金资产价值
    asset_value: Decimal = 0

    # available_funds + asset_value
    total_assets: Decimal = 0

    # 当前周期真实收入
    income: Decimal = 0

    # 当前周期真实消费
    expense: Decimal = 0

    # income - expense
    balance: Decimal = 0

    # 储蓄率
    saving_rate: Decimal | None
    

    # 与上一周期相比
    previous_income: Decimal = 0
    previous_expense: Decimal = 0
    previous_balance: Decimal = 0
    income_change: Decimal | None
    expense_change: Decimal | None
    balance_change: Decimal | None
    total_assets_change: Decimal | None
    income_change_rate: Decimal | None    # 收入环比
    expense_change_rate: Decimal | None    # 支出环比
    total_assets_change_rate: Decimal | None   # 总资产环比



class CashFlowTrendItem(BaseModel):
    bucket_date: date
    income: Decimal
    expense: Decimal
    balance: Decimal


class CashFlowTrend(BaseModel):
    items: list[CashFlowTrendItem]



class ExpenseCategoryItem(BaseModel):
    category_id: str | None
    category_name: str

    amount: Decimal

    # 0 ~ 1
    percentage: Decimal

    transaction_count: int

    change: Decimal | None = None

    # 环比
    change_rate: Decimal | None = None


class ExpenseCategoryStatistics(BaseModel):
    total: Decimal
    items: list[ExpenseCategoryItem]


class AccountDistributionItem(BaseModel):
    id: str
    name: str
    type: AccountType

    balance: Decimal
    available_balance: Decimal
    percentage: Decimal


class AccountDistribution(BaseModel):
    total: Decimal
    items: list[AccountDistributionItem]


class AssetCategoryItem(BaseModel):
    category_id: str
    category_name: str

    value: Decimal
    percentage: Decimal

    asset_count: int


class AssetDistribution(BaseModel):
    total: Decimal
    items: list[AssetCategoryItem]


class WealthTrendItem(BaseModel):
    bucket_date: date

    # 银行/微信/支付宝/现金
    account_value: Decimal

    # 房产/汽车/其他资产
    asset_value: Decimal

    # 两者相加
    total_assets: Decimal


class WealthTrend(BaseModel):
    items: list[WealthTrendItem]

class FinancialInsight(BaseModel):
    id: str

    type: InsightType
    level: InsightLevel

    title: str
    description: str

    value: Decimal | None = None
    change_rate: Decimal | None = None
    

class FinancialInsights(BaseModel):
    items: list[FinancialInsight]


class DashboardOverview(BaseModel):
    metrics: DashboardMetrics

    cash_flow_trend: CashFlowTrend

    expense_categories: ExpenseCategoryStatistics

    accounts: AccountDistribution

    assets: AssetDistribution

    wealth_trend: WealthTrend

    insights: FinancialInsights | None = None
