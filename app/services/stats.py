from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import List
from typing_extensions import Sequence
from dateutil.relativedelta import relativedelta
from app.constant import AssetStatus, TransactionType
from app.models.asset import Account
from app.models.base import BaseModel
from app.repo.account import account_repo
from app.repo.asset import asset_repo, wealth_snapshot_repo
from app.repo.category import category_repo
from app.repo.transaction import transaction_repo
from app.schemas.stats import (
    AccountDistribution,
    AccountDistributionItem,
    AssetCategoryItem,
    AssetDistribution,
    CashFlowTrend,
    CashFlowTrendItem,
    DashboardMetrics,
    DashboardPeriod,
    DashboardQuery,
    DateRange,
    ExpenseCategoryItem,
    ExpenseCategoryStatistics,
    WealthTrend,
    WealthTrendItem,
)
from app.services.cache.stats import OverviewMetricsCache


CENT = Decimal("100")


def cents_to_yuan(
    value: int | None,
) -> Decimal | None:
    if value is None:
        return None

    return Decimal(value) / CENT


class StatsService:
    @staticmethod
    async def get_category_mapping(session, user_id, cids: Sequence[str]):
        category_list = await category_repo.list_by_user(session, user_id, ids=cids)
        return {c.id: c for c in category_list}

    @staticmethod
    def resolve_period_with_previous(
        target_date: date,
        period: DashboardPeriod,
        today: date | None = None,
    ) -> tuple[DateRange, DateRange]:

        today = today or date.today()

        # 1. 找到完整周期边界
        if period == DashboardPeriod.MONTH:
            period_start = target_date.replace(day=1)
            period_end = period_start + relativedelta(months=1)

            previous_start = period_start - relativedelta(months=1)

        elif period == DashboardPeriod.QUARTER:
            month = ((target_date.month - 1) // 3) * 3 + 1

            period_start = date(
                target_date.year,
                month,
                1,
            )
            period_end = period_start + relativedelta(months=3)

            previous_start = period_start - relativedelta(months=3)

        elif period == DashboardPeriod.YEAR:
            period_start = date(target_date.year, 1, 1)
            period_end = date(target_date.year + 1, 1, 1)

            previous_start = date(target_date.year - 1, 1, 1)

        else:
            raise ValueError("Unsupported period")

        # 2. 如果查询的是当前周期，只统计到今天
        is_current_period = period_start <= today < period_end

        if is_current_period:
            # end 是 exclusive，所以包含今天
            current_end = today + timedelta(days=1)

            elapsed_days = (current_end - period_start).days

            previous_end = previous_start + timedelta(days=elapsed_days)

        else:
            current_end = period_end

            previous_end = period_start

        return (
            DateRange(
                start_date=period_start,
                end_date=current_end,
            ),
            DateRange(
                start_date=previous_start,
                end_date=previous_end,
            ),
        )

    def calc_change(
        current: Decimal,
        previous: Decimal,
    ) -> tuple[Decimal, Decimal | None]:

        change = current - previous

        if previous == 0:
            return change, None

        rate = (change / abs(previous)).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
        )

        return change, rate

    @classmethod
    async def get_overview(cls, session, cur_user, query: DashboardQuery): ...

    @classmethod
    async def get_metrics(cls, session, cur_user, query: DashboardQuery) -> DashboardMetrics:
        user_id = cur_user.id
        cache_key = query.to_cache_key()
        ret = await OverviewMetricsCache(user_id, cache_key).get()
        if ret:
            return ret

        target_date = query.query_date or date.today()

        current_range, previous_range = cls.resolve_period_with_previous(
            target_date, query.period, query.query_date
        )

        income = await transaction_repo.sum_amount(
            session,
            user_id,
            transaction_type=[
                TransactionType.INCOME,
                TransactionType.BORROW_IN,
            ],
            start_time=current_range.start_date,
            end_time=current_range.end_date,
        )

        expense = await transaction_repo.sum_amount(
            session,
            user_id,
            transaction_type=[
                TransactionType.EXPENSE,
                TransactionType.BORROW_OUT,
                TransactionType.REPAYMENT,
            ],
            start_time=current_range.start_date,
            end_time=current_range.end_date,
        )

        previous_income = await transaction_repo.sum_amount(
            session,
            user_id,
            transaction_type=[
                TransactionType.INCOME,
                TransactionType.BORROW_IN,
            ],
            start_time=previous_range.start_date,
            end_time=previous_range.end_date,
        )

        previous_expense = await transaction_repo.sum_amount(
            session,
            user_id,
            transaction_type=[
                TransactionType.EXPENSE,
                TransactionType.BORROW_OUT,
                TransactionType.REPAYMENT,
            ],
            start_time=previous_range.start_date,
            end_time=previous_range.end_date,
        )

        balance = income - expense
        previous_balance = previous_income - previous_expense

        available_funds = await account_repo.sum_balance(session, user_id)

        asset_value = await asset_repo.asset_summary(session, user_id, AssetStatus.NORMAL)

        total_assets = available_funds + asset_value
        previous_wealth_snapshot = await wealth_snapshot_repo.retrieve(
            session, user_id, previous_range.start_date
        )
        if previous_wealth_snapshot:
            total_assets_change = total_assets - previous_wealth_snapshot.total_assets
            total_assets_change_rate = (
                total_assets_change / previous_wealth_snapshot.total_assets
                if previous_wealth_snapshot.total_assets != 0
                else None
            )
        else:
            total_assets_change = total_assets_change_rate = None

        saving_rate = balance / income if income > 0 else None

        income_change, income_change_rate = cls.calc_change(income, previous_income)

        expense_change, expense_change_rate = cls.calc_change(expense, previous_expense)

        balance_change = balance - previous_balance

        ret = DashboardMetrics(
            available_funds=cents_to_yuan(available_funds),
            total_assets=cents_to_yuan(total_assets),
            asset_value=cents_to_yuan(asset_value),
            income=cents_to_yuan(income),
            expense=cents_to_yuan(expense),
            balance=cents_to_yuan(balance),
            saving_rate=saving_rate,
            previous_balance=cents_to_yuan(previous_balance),
            previous_income=cents_to_yuan(previous_income),
            previous_expense=cents_to_yuan(previous_expense),
            income_change=cents_to_yuan(income_change),
            expense_change=cents_to_yuan(expense_change),
            balance_change=cents_to_yuan(balance_change),
            total_assets_change=cents_to_yuan(total_assets_change),
            income_change_rate=income_change_rate,
            expense_change_rate=expense_change_rate,
            total_assets_change_rate=total_assets_change_rate,
        )

        await OverviewMetricsCache(user_id, cache_key).add(ret)
        return ret

    @classmethod
    async def get_cash_flow(cls, session, cur_user, query: DashboardQuery):
        current_range, _ = cls.resolve_period_with_previous(
            query.query_date or date.today(), query.period, query.query_date
        )
        rows = await transaction_repo.aggregate_cash_flow(
            session=session,
            user_id=cur_user.id,
            start=current_range.start_date,
            end=current_range.end_date,
            granularity=query.granularity,
        )

        items = []

        for row in rows:
            # date_trunc(month) PostgreSQL 返回 datetime
            bucket_date = row.bucket

            if isinstance(bucket_date, datetime):
                bucket_date = bucket_date.date()

            items.append(
                CashFlowTrendItem(
                    bucket_date=bucket_date,
                    income=cents_to_yuan(row.income),
                    expense=cents_to_yuan(row.expense),
                    balance=cents_to_yuan(row.income - row.expense),
                )
            )

        return CashFlowTrend(items=items)

    @classmethod
    async def get_expense_category(cls, session, cur_user, query: DashboardQuery):
        cur_range, prev_range = cls.resolve_period_with_previous(
            query.query_date or date.today(), query.period, query.query_date
        )
        cur_rows = await transaction_repo.agg_expense_category(
            session, cur_user.id, cur_range.start_date, cur_range.end_date
        )

        prev_rows = await transaction_repo.agg_expense_category(
            session, cur_user.id, prev_range.start_date, prev_range.end_date
        )

        category_mapping = await cls.get_category_mapping(
            session, cur_user.id, {i.category_id for i in cur_rows + prev_rows}
        )

        cur_total = sum(
            (Decimal(row.amount or 0) for row in cur_rows),
            Decimal("0"),
        )
        prev_total = sum(
            (Decimal(row.amount or 0) for row in prev_rows),
            Decimal("0"),
        )

        prev_map = {row.category_id: Decimal(row.amount or 0) for row in prev_rows}

        # 4. 计算占比并格式化（核心优雅之处）
        items: list[ExpenseCategoryItem] = []

        for item in cur_rows:
            amount = Decimal(item.amount or 0)

            if cur_total > 0:
                percentage = (Decimal(amount) / Decimal(cur_total)).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
            else:
                percentage = Decimal("0")

            prev_amount = prev_map.get(item.category_id, Decimal("0"))

            change, rate = cls.calc_change(
                amount,
                prev_amount,
            )
            category = category_mapping.get(item.category_id)

            item = ExpenseCategoryItem(
                category_id=item.category_id,
                category_name=category.name if category else None,
                amount=cents_to_yuan(amount),
                transaction_count=item.transaction_count,
                percentage=percentage,
                change=cents_to_yuan(change),
                change_rate=rate,
            )

            items.append(item)

        items.sort(
            key=lambda item: item.amount,
            reverse=True,
        )

        return ExpenseCategoryStatistics(
            total=cents_to_yuan(cur_total),
            items=items,
        )

    @classmethod
    async def get_account_stats(
        cls,
        session,
        cur_user,
    ):
        rows: List[Account] = await account_repo.list(session, cur_user.id)

        total_balance = sum((a.balance for a in rows))

        items = []
        for item in rows:
            if total_balance > 0:
                percentage = (Decimal(item.balance) / Decimal(total_balance)).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
            else:
                percentage = Decimal("0")

            items.append(
                AccountDistributionItem(
                    id=item.id,
                    name=item.name,
                    type=item.account_type,
                    balance=cents_to_yuan(item.balance),
                    available_balance=cents_to_yuan(item.available_balance),
                    percentage=percentage,
                )
            )

        items.sort(key=lambda item: item.available_balance, reverse=True)

        return AccountDistribution(
            total=cents_to_yuan(total_balance),
            items=items,
        )

    @classmethod
    async def get_asset_category_stats(cls, session, cur_user):
        rows = await asset_repo.get_asset_category_stats(session, cur_user.id)
        category_mapping = await cls.get_category_mapping(
            session, cur_user.id, {i.category_id for i in rows}
        )
        total_value = sum((a.current_value for a in rows))

        items = []
        for item in rows:
            if total_value > 0:
                percentage = (Decimal(item.current_value) / Decimal(total_value)).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
            else:
                percentage = Decimal("0")

            category = category_mapping.get(item.category_id)

            items.append(
                AssetCategoryItem(
                    category_id=item.category_id,
                    category_name=category.name if category else None,
                    value=cents_to_yuan(item.current_value),
                    percentage=percentage,
                    asset_count=item.asset_count,
                )
            )

        return AssetDistribution(total=cents_to_yuan(total_value), items=items)

    @classmethod
    async def get_wealth_trend(cls, session, cur_user, query: DashboardQuery):
        current_range, _ = cls.resolve_period_with_previous(
            query.query_date or date.today(), query.period, query.query_date
        )

        rows = await wealth_snapshot_repo.agg_wealth_flow(
            session,
            cur_user.id,
            query.granularity,
            current_range.start_date,
            current_range.end_date,
        )

        items = []

        for item in rows:
            items.append(
                WealthTrendItem(
                    bucket_date=item.bucket,
                    asset_value=cents_to_yuan(item.asset_value),
                    account_value=cents_to_yuan(item.account_value),
                    total_assets=cents_to_yuan(item.total_assets),
                )
            )

        return WealthTrend(items=items)
