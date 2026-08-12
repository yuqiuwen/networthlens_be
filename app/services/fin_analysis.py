from datetime import datetime

from app.constant import (
    LiabilityStatus,
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
    FinancialSnapshotResult,
    GoalAnalysisQuery,
    GoalAnalysisResult,
    GoalForecastItem,
    LiabilityAnalysisQuery,
    LiabilityAnalysisResult,
    NetWorthAnalysisResult,
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

    async def expense_analysis(
        self,
        session,
        user_id: int,
        query: ExpenseAnalysisQuery,
    ):
        income = (
            await fin_analysis_repo.sum_transaction_amount(
                session,
                user_id,
                transaction_type=TransactionType.INCOME,
                start_time=query.start_time,
                end_time=query.end_time,
            )
        )

        expense = (
            await fin_analysis_repo.sum_transaction_amount(
                session,
                user_id,
                transaction_type=TransactionType.EXPENSE,
                start_time=query.start_time,
                end_time=query.end_time,
            )
        )

        category_rows = (
            await fin_analysis_repo.expense_by_category(
                session,
                user_id,
                start_time=query.start_time,
                end_time=query.end_time,
            )
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
        )

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
