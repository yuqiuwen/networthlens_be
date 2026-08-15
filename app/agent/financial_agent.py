from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings


from app.agent.context_builder import ContextBuilder, FinancialInstructionBuilder
from app.agent.deps import FinAgentDeps
from app.agent.prompts import (
    FINANCIAL_INSTRUCTIONS,
)
from app.agent.tools import fin_analysis
from app.config import settings


context_builder = ContextBuilder()

financial_agent = Agent(
    settings.MODEL_CHAT,
    deps_type=FinAgentDeps,
    instructions=FINANCIAL_INSTRUCTIONS,
    model_settings=ModelSettings(timeout=300),
    tools=[
        fin_analysis.expense_analysis,
        fin_analysis.transaction_rank,
        fin_analysis.net_worth_analysis,
        fin_analysis.asset_analysis,
        fin_analysis.liability_analysis,
        fin_analysis.goal_analysis,
        fin_analysis.financial_snapshot,
    ],
)

# @financial_agent.system_prompt
# async def dynamic_financial_context(
#     ctx: RunContext[FinAgentDeps],
# ):
#     """
#     动态财务上下文

#     每次Agent运行时构建

#     内容来自：
#         FinancialAnalysisService

#     目的：
#         给模型实时财务快照

#     不依赖历史消息
#     """

#     return await context_builder.build_system_context(
#         ctx.deps.session,
#         ctx.deps.user_id,
#     )


@financial_agent.instructions
async def build_runtime_instruction(
    ctx: RunContext[FinAgentDeps],
):
    return await FinancialInstructionBuilder.build(
        ctx.deps.session,
        ctx.deps.user_id,
    )




#
#     AgentContextBuilder
#     ↓
# 历史聊天

# FinancialInstructionBuilder
#     ↓
# 实时财务上下文

# FINANCIAL_INSTRUCTIONS
#     ↓
# 固定行为规则

# FinancialAnalysisService
#     ↓
# 详细财务分析

# Tool
#     ↓
# 让模型按需获取详细数据
