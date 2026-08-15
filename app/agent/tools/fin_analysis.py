from datetime import datetime
from typing import Literal

from pydantic_ai import RunContext

from app.agent.deps import FinAgentDeps
from app.schemas.fin_analysis import (
    AssetAnalysisQuery,
    ExpenseAnalysisQuery,
    GoalAnalysisQuery,
    LiabilityAnalysisQuery,
    TransactionRankQuery,
)


async def expense_analysis(
    ctx: RunContext[FinAgentDeps],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    granularity: Literal["week", "month", "year"] = "month",
    period_count: int | None = None,
) -> dict:
    """Analyze income and expenses with weekly, monthly, or yearly trend buckets."""
    result = (
        await ctx.deps.analysis_service.expense_analysis(
            ctx.deps.session,
            ctx.deps.user_id,
            ExpenseAnalysisQuery(
                start_time=start_time,
                end_time=end_time,
                granularity=granularity,
                period_count=period_count,
            ),
        )
    )

    return result.model_dump()


async def transaction_rank(
    ctx: RunContext[FinAgentDeps],
    time_range: Literal["this_week", "this_month", "this_year"] | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    transaction_type: Literal["income", "expense"] = "expense",
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = 10,
    currency: str = "CNY",
    include_refunded: bool = False,
) -> dict:
    """Query the largest or smallest individual income or expense transactions.

    Use time_range for this week, month, or year. Use explicit start_time and
    end_time for a custom range. The default finds the largest expenses.
    """
    result = await ctx.deps.analysis_service.transaction_rank(
        ctx.deps.session,
        ctx.deps.user_id,
        TransactionRankQuery(
            time_range=time_range,
            start_time=start_time,
            end_time=end_time,
            transaction_type=transaction_type,
            sort_order=sort_order,
            limit=limit,
            currency=currency,
            include_refunded=include_refunded,
        ),
    )
    return result.model_dump()


async def asset_analysis(
    ctx: RunContext[FinAgentDeps],
):
    result = (
        await ctx.deps.analysis_service.asset_analysis(
            ctx.deps.session,
            ctx.deps.user_id,
            AssetAnalysisQuery(),
        )
    )

    return result.model_dump()
    

async def net_worth_analysis(
    ctx: RunContext[FinAgentDeps],
):
    result = (
        await ctx.deps.analysis_service.net_worth(
            ctx.deps.session,
            ctx.deps.user_id,
        )
    )

    return result.model_dump()


async def liability_analysis(
    ctx: RunContext[FinAgentDeps],
):
    result = (
        await ctx.deps.analysis_service.liability_analysis(
            ctx.deps.session,
            ctx.deps.user_id,
            LiabilityAnalysisQuery(),
        )
    )

    return result.model_dump()


async def goal_analysis(
    ctx: RunContext[FinAgentDeps],
):
    result = (
        await ctx.deps.analysis_service.goal_analysis(
            ctx.deps.session,
            ctx.deps.user_id,
            GoalAnalysisQuery(),
        )
    )

    return result.model_dump()


async def financial_snapshot(
    ctx: RunContext[FinAgentDeps],
):
    result = (
        await ctx.deps.analysis_service.snapshot(
            ctx.deps.session,
            ctx.deps.user_id,
        )
    )

    return result
