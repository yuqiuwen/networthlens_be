from datetime import datetime
from datetime import timedelta

from pydantic_ai import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agent.constant import AgentRole
from app.models.chat import AIChatMessage
from app.schemas.fin_analysis import (
    AssetAnalysisQuery,
    ExpenseAnalysisQuery,
    LiabilityAnalysisQuery,
)
from app.services.fin_analysis import (
    FinancialAnalysisService,
)


class ContextBuilder:
    """
    Agent上下文构建器

    职责：

    1. 构建动态系统上下文
    2. 构建财务快照
    3. 构建消费分析上下文
    4. 构建资产分析上下文
    5. 控制上下文长度

    注意：

    Agent不要直接把数据库原始数据塞给LLM

    应该：

        DB
        ↓
        Analysis Service
        ↓
        Context Builder
        ↓
        Prompt
        ↓
        LLM
    """

    def __init__(self):
        self.analysis_service = FinancialAnalysisService()

    @staticmethod
    def _build_message(
        message: AIChatMessage,
    ) -> ModelMessage | None:
        if message.role == AgentRole.USER:
            return ModelRequest(
                parts=[
                    UserPromptPart(
                        content=message.content,
                    )
                ]
            )

        if message.role == AgentRole.ASSISTANT:
            return ModelResponse(
                parts=[
                    TextPart(
                        content=message.content,
                    )
                ]
            )

        return None


    @classmethod
    def build_messages(cls, messages):
        """
        将数据库中的聊天记录转换成
        PydanticAI message_history
        """

        result = []

        for item in messages:
            model_message = cls._build_message(item)

            if model_message is not None:
                result.append(
                    model_message
                )

        return result

    async def financial_snapshot(
        self,
        session,
        user_id: int,
    ):
        """
        用户财务总览

        Agent每次对话都可以使用
        """

        snapshot = await self.analysis_service.snapshot(
            session,
            user_id,
        )

        snapshot = snapshot.model_dump()

        return f"""
用户财务概况：

总资产：
{snapshot["total_asset"]}

总负债：
{snapshot["total_liability"]}

净资产：
{snapshot["net_worth"]}

资产数量：
{snapshot["asset_count"]}

负债数量：
{snapshot["liability_count"]}
"""

    async def expense_snapshot(
        self,
        session,
        user_id: int,
        days: int = 30,
    ):
        """
        最近消费概览
        """

        end_time = datetime.now()

        start_time = end_time - timedelta(days=days)

        result = await self.analysis_service.expense_analysis(
            session,
            user_id,
            ExpenseAnalysisQuery(
                start_time=start_time,
                end_time=end_time,
            ),
        )

        result = result.model_dump()

        if not result["top_categories"]:
            category_text = "暂无支出数据"
        else:
            category_text = "\n".join(
                [
                    (f"- {item["category_name"] or '未分类'} {item["amount"]}")
                    for item in result["top_categories"][:5]
                ]
            )

        return f"""
最近{days}天收支：

收入：
{result["income"]}

支出：
{result["expense"]}

结余：
{result["balance"]}

主要支出分类：

{category_text}
"""

    async def asset_snapshot(
        self,
        session,
        user_id: int,
    ):
        """
        资产配置概览
        """

        result = await self.analysis_service.asset_analysis(
            session,
            user_id,
            AssetAnalysisQuery(),
        )

        result = result.model_dump()

        if not result["allocations"]:
            return """
当前暂无资产数据
"""

        allocation_text = "\n".join(
            [
                (f"- {item["asset_name"]} {item["amount"]} ({item["ratio"] * 100:.2f}%)")
                for item in result["allocations"][:10]
            ]
        )

        return f"""
资产配置：

总资产：

{result["total_asset"]}

资产构成：

{allocation_text}
"""

    async def liability_snapshot(
        self,
        session,
        user_id: int,
    ):
        """
        负债概览
        """

        result = await self.analysis_service.liability_analysis(
            session,
            user_id,
            LiabilityAnalysisQuery(),
        )

        result = result.model_dump()

        return f"""
负债情况：

负债总额：

{result["total_liability"]}

生效负债：

{result["active_count"]}

已结清负债：

{result["settled_count"]}
"""

    async def build_system_context(
        self,
        session,
        user_id: int,
    ):
        """
        Agent动态上下文

        每次Agent运行都会构建
        """

        financial_context = await self.financial_snapshot(
            session,
            user_id,
        )

        expense_context = await self.expense_snapshot(
            session,
            user_id,
        )

        asset_context = await self.asset_snapshot(
            session,
            user_id,
        )

        liability_context = await self.liability_snapshot(
            session,
            user_id,
        )

        return f"""
以下是当前用户实时财务数据。

你必须优先使用这些真实数据回答问题。

====================

{financial_context}

====================

{expense_context}

====================

{asset_context}

====================

{liability_context}

====================

回答要求：

1. 使用真实数据分析
2. 无法确定时明确说明
3. 不编造资产数据
4. 不提供投资承诺
5. 不推荐具体证券买卖
6. 金额单位自动转换为元展示
7. 回答尽量简洁
"""



class FinancialInstructionBuilder:
    """
    动态财务 Instructions 构建器。

    这里只提供每次 Agent Run 都可能发生变化的实时业务上下文。

    固定行为规则放在 FINANCIAL_INSTRUCTIONS 中，
    不在这里重复。

    注意：
    动态上下文应该保持精简。
    详细分析由 Agent 根据用户问题调用 Tool 获取，
    不应该在每次聊天时把所有财务数据都加载进上下文。
    """

    @classmethod
    async def build(
        cls,
        session,
        user_id: int,
    ) -> str:
        analysis_service = FinancialAnalysisService()

        snapshot = await analysis_service.snapshot(
            session=session,
            user_id=user_id,
        )

        snapshot = snapshot.model_dump()

        total_asset = snapshot.get("total_asset", 0)
        total_liability = snapshot.get("total_liability", 0)
        net_worth = snapshot.get("net_worth", 0)
        asset_count = snapshot.get("asset_count", 0)
        liability_count = snapshot.get("liability_count", 0)

        return f"""
当前用户实时财务概况：

- 总资产：{total_asset} 元
- 总负债：{total_liability} 元
- 净资产：{net_worth} 元
- 资产数量：{asset_count}
- 负债数量：{liability_count}

以上数据是当前运行时的财务快照。

如果用户询问更加详细的数据，例如特定时间段的消费、
资产配置、负债详情或目标完成情况，请调用对应工具获取，
不要仅根据这份概要自行推断。
""".strip()