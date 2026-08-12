from pydantic_ai import RunContext

from datetime import datetime
from app.agent.deps import FinAgentDeps
from app.schemas.fin_analysis import AssetAnalysisQuery, ExpenseAnalysisQuery, GoalAnalysisQuery, LiabilityAnalysisQuery


async def expense_analysis(
    ctx: RunContext[FinAgentDeps],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    result = (
        await ctx.deps.analysis_service.expense_analysis(
            ctx.deps.session,
            ctx.deps.user_id,
            ExpenseAnalysisQuery(
                start_time=start_time,
                end_time=end_time,
            ),
        )
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