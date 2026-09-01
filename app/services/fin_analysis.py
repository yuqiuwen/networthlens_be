from datetime import datetime, time, timedelta

from app.constant import (
    LiabilityStatus,
    TransactionStatus,
    TransactionType,
)
from app.repo.fin_analysis import (
    fin_analysis_repo,
)
from app.schemas.fin_analysis import (
    AssetAllocationItem,
    AssetAnalysisQuery,
    AssetAnalysisResult,
    ExpenseAnalysisQuery,
    ExpenseAnalysisResult,
    ExpenseCategoryItem,
    ExpenseTrendItem,
    FinancialSnapshotResult,
    GoalAnalysisQuery,
    GoalAnalysisResult,
    GoalForecastItem,
    LiabilityAnalysisQuery,
    LiabilityAnalysisResult,
    NetWorthAnalysisResult,
    TransactionRankItem,
    TransactionRankQuery,
    TransactionRankResult,
)


class FinancialAnalysisService:
    """
    财务分析服务

    给 Agent 提供结构化分析结果

    不返回 ORM
    不返回 SQL
    不返回原始流水
    """

    # ==========================
    # 净资产分析
    # ==========================

    async def net_worth(
        self,
        session,
        user_id: int,
    ):
        total_asset = (
            await fin_analysis_repo.total_asset(
                session,
                user_id,
            )
        )

        total_liability = (
            await fin_analysis_repo.total_liability(
                session,
                user_id,
            )
        )

        return NetWorthAnalysisResult(
            total_asset=total_asset,
            total_liability=total_liability,
            net_worth=(
                total_asset
                - total_liability
            ),
        )

    # ==========================
    # 收支分析
    # ==========================

    async def transaction_rank(
        self,
        session,
        user_id: int,
        query: TransactionRankQuery,
    ) -> TransactionRankResult:
        """Return the highest or lowest individual transactions in a time range."""
        transaction_type = {
            "income": TransactionType.INCOME,
            "expense": TransactionType.EXPENSE,
        }[query.transaction_type]
        start_time, end_time = self._resolve_rank_range(query)
        rows = await fin_analysis_repo.rank_transactions(
            session,
            user_id,
            transaction_type=transaction_type,
            currency=query.currency,
            sort_order=query.sort_order,
            limit=query.limit,
            start_time=start_time,
            end_time=end_time,
            include_refunded=query.include_refunded,
        )

        return TransactionRankResult(
            transaction_type=query.transaction_type,
            sort_order=query.sort_order,
            currency=query.currency,
            include_refunded=query.include_refunded,
            start_time=start_time,
            end_time=end_time,
            items=[
                TransactionRankItem(
                    rank=index,
                    category_id=row.category_id,
                    category_name=row.category_name,
                    amount=row.amount,
                    currency=row.currency,
                    merchant=row.merchant,
                    product=row.product,
                    occurred_at=row.occurred_at,
                    status=TransactionStatus(row.status).desc,
                )
                for index, row in enumerate(rows, start=1)
            ],
        )

    async def expense_analysis(
        self,
        session,
        user_id: int,
        query: ExpenseAnalysisQuery,
    ):
        start_time, end_time = self._resolve_expense_range(query)

        income = (
            await fin_analysis_repo.sum_transaction_amount(
                session,
                user_id,
                transaction_type=TransactionType.INCOME,
                start_time=start_time,
                end_time=end_time,
                category_ids=query.category_ids,
                source_account_ids=query.source_account_ids,
                target_account_ids=query.target_account_ids,
            )
        )

        expense = (
            await fin_analysis_repo.sum_transaction_amount(
                session,
                user_id,
                transaction_type=TransactionType.EXPENSE,
                start_time=start_time,
                end_time=end_time,
                category_ids=query.category_ids,
                source_account_ids=query.source_account_ids,
                target_account_ids=query.target_account_ids,
            )
        )

        category_rows = (
            await fin_analysis_repo.expense_by_category(
                session,
                user_id,
                start_time=start_time,
                end_time=end_time,
                category_ids=query.category_ids,
                source_account_ids=query.source_account_ids,
                target_account_ids=query.target_account_ids,
            )
        )

        trend_rows = await fin_analysis_repo.sum_transaction_by_period(
            session,
            user_id,
            granularity=query.granularity,
            start_time=start_time,
            end_time=end_time,
            category_ids=query.category_ids,
            source_account_ids=query.source_account_ids,
            target_account_ids=query.target_account_ids,
        )

        categories = []

        if expense > 0:
            for row in category_rows:
                categories.append(
                    ExpenseCategoryItem(
                        category_id=row.category_id,
                        category_name=row.name,
                        amount=row.amount,
                        ratio=round(
                            row.amount / expense,
                            4,
                        ),
                    )
                )

        return ExpenseAnalysisResult(
            income=income,
            expense=expense,
            balance=income - expense,
            top_categories=categories,
            granularity=query.granularity,
            trend=self._build_expense_trend(
                trend_rows,
                granularity=query.granularity,
                start_time=start_time,
                end_time=end_time,
            ),
        )

    @staticmethod
    def _resolve_rank_range(
        query: TransactionRankQuery,
    ) -> tuple[datetime | None, datetime | None]:
        """Resolve a relative time range when explicit timestamps are absent."""
        if query.start_time is not None or query.end_time is not None:
            return query.start_time, query.end_time

        if query.time_range is None:
            return None, None

        end_time = datetime.now()
        if query.time_range == "this_week":
            start_time = end_time - timedelta(days=end_time.weekday())
            start_time = start_time.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        elif query.time_range == "this_month":
            start_time = end_time.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            start_time = end_time.replace(
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        return start_time, end_time

    @staticmethod
    def _resolve_expense_range(
        query: ExpenseAnalysisQuery,
    ) -> tuple[datetime | None, datetime | None]:
        """Resolve an optional number of recent calendar periods into a time range."""
        start_time = query.start_time
        end_time = query.end_time

        if query.period_count:
            end_time = end_time or datetime.now()
            if start_time is None:
                end_bucket = FinancialAnalysisService._period_start(
                    end_time,
                    query.granularity,
                )
                start_time = FinancialAnalysisService._shift_period(
                    end_bucket,
                    query.granularity,
                    -(query.period_count - 1),
                )

        return start_time, end_time

    @staticmethod
    def _period_start(value: datetime, granularity: str) -> datetime:
        """Return the beginning of the calendar bucket containing a timestamp."""
        value = value.replace(hour=0, minute=0, second=0, microsecond=0)
        if granularity == "week":
            return value - timedelta(days=value.weekday())
        if granularity == "month":
            return value.replace(day=1)
        return value.replace(month=1, day=1)

    @staticmethod
    def _shift_period(value: datetime, granularity: str, count: int) -> datetime:
        """Shift a bucket start by a number of calendar periods."""
        if granularity == "week":
            return value + timedelta(weeks=count)
        if granularity == "month":
            month_index = value.year * 12 + value.month - 1 + count
            year, month_index = divmod(month_index, 12)
            return value.replace(year=year, month=month_index + 1, day=1)
        return value.replace(year=value.year + count, month=1, day=1)

    @classmethod
    def _build_expense_trend(
        cls,
        rows,
        *,
        granularity: str,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[ExpenseTrendItem]:
        """Build ordered trend items and fill missing buckets within a bounded range."""
        values = {}
        for row in rows:
            period = row.period
            if not isinstance(period, datetime):
                period = datetime.combine(period, time.min)
            label = cls._period_label(period, granularity)
            income = int(row.income or 0)
            expense = int(row.expense or 0)
            values[label] = (income, expense)

        if start_time is not None and end_time is not None and start_time <= end_time:
            period = cls._period_start(start_time, granularity)
            end_period = cls._period_start(end_time, granularity)
            while period <= end_period:
                label = cls._period_label(period, granularity)
                values.setdefault(label, (0, 0))
                period = cls._shift_period(period, granularity, 1)

        return [
            ExpenseTrendItem(
                period=label,
                income=income,
                expense=expense,
                balance=income - expense,
            )
            for label, (income, expense) in sorted(values.items())
        ]

    @staticmethod
    def _period_label(value: datetime, granularity: str) -> str:
        if granularity == "week":
            return value.strftime("%G-W%V")
        if granularity == "month":
            return value.strftime("%Y-%m")
        return value.strftime("%Y")

    # ==========================
    # 资产分析
    # ==========================

    async def asset_analysis(
        self,
        session,
        user_id: int,
        query: AssetAnalysisQuery,
    ):
        assets = (
            await fin_analysis_repo.query_assets(
                session,
                user_id,
                asset_types=query.asset_types,
                category_ids=query.category_ids
            )
        )

        total_asset = sum(
            item.current_value
            for item in assets
        )

        allocations = []

        if total_asset > 0:
            for item in assets:
                allocations.append(
                    AssetAllocationItem(
                        asset_type=item.asset_type,
                        asset_name=item.name,
                        category_id=item.category_id,
                        category=item.category,
                        amount=item.current_value,
                        ratio=round(
                            item.current_value
                            / total_asset,
                            4,
                        ),
                    )
                )

        allocations.sort(
            key=lambda x: x.amount,
            reverse=True,
        )

        return AssetAnalysisResult(
            total_asset=total_asset,
            allocations=allocations,
        )

    # ==========================
    # 负债分析
    # ==========================

    async def liability_analysis(
        self,
        session,
        user_id: int,
        query: LiabilityAnalysisQuery,
    ):
        liabilities = (
            await fin_analysis_repo.query_liabilities(
                session,
                user_id,
                liability_types=query.liability_types,
            )
        )

        total_liability = 0

        active_count = 0

        settled_count = 0

        for item in liabilities:
            if (
                item.status
                == LiabilityStatus.ACTIVE
            ):
                active_count += 1

                total_liability += (
                    item.remaining_principal
                )

            elif (
                item.status
                == LiabilityStatus.SETTLED
            ):
                settled_count += 1

        return LiabilityAnalysisResult(
            total_liability=total_liability,
            active_count=active_count,
            settled_count=settled_count,
        )

    # ==========================
    # 目标分析
    # ==========================

    async def goal_analysis(
        self,
        session,
        user_id: int,
        query: GoalAnalysisQuery,
    ):
        goals = (
            await fin_analysis_repo.query_goals(
                session,
                user_id,
                goal_ids=query.goal_ids,
            )
        )

        expense_result = (
            await self.expense_analysis(
                session,
                user_id,
                ExpenseAnalysisQuery(
                    start_time=query.start_time,
                    end_time=query.end_time,
                ),
            )
        )

        avg_monthly_saving = (
            expense_result.balance
        )

        result = []

        for item in goals:
            remaining_amount = (
                item.target_amount
                - item.current_amount
            )

            estimated_months = None

            if (
                avg_monthly_saving > 0
                and remaining_amount > 0
            ):
                estimated_months = (
                    remaining_amount
                    // avg_monthly_saving
                )

            result.append(
                GoalForecastItem(
                    goal_id=item.id,
                    goal_name=item.name,
                    target_amount=item.target_amount,
                    current_amount=item.current_amount,
                    remaining_amount=remaining_amount,
                    estimated_months=estimated_months,
                )
            )

        return GoalAnalysisResult(
            goals=result,
        )

    # ==========================
    # Dashboard Snapshot
    # ==========================

    async def snapshot(
        self,
        session,
        user_id: int,
    ):
        """
        Agent最常调用的上下文快照

        用于System Prompt动态上下文
        """

        net_worth = await self.net_worth(
            session,
            user_id,
        )

        liability = (
            await self.liability_analysis(
                session,
                user_id,
                LiabilityAnalysisQuery(),
            )
        )

        asset = await self.asset_analysis(
            session,
            user_id,
            AssetAnalysisQuery(),
        )

        return FinancialSnapshotResult(
            total_asset=net_worth.total_asset,
            total_liability=net_worth.total_liability,
            net_worth=net_worth.net_worth,
            asset_count=len(asset.allocations),
            liability_count=(
                liability.active_count
                + liability.settled_count
            ),
        )
