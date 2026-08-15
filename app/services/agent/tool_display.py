
TOOL_DISPLAY_NAMES = {
    "expense_analysis": "收支分析",
    "transaction_rank": "流水金额排名",
    "net_worth_analysis": "净资产分析",
    "asset_analysis": "资产配置分析",
    "liability_analysis": "负债分析",
    "goal_analysis": "财务目标分析",
    "financial_snapshot": "财务概况",
}


TOOL_RUNNING_MESSAGES = {
    "expense_analysis": "正在分析你的收支情况",
    "transaction_rank": "正在查询单笔流水金额排名",
    "net_worth_analysis": "正在计算你的净资产",
    "asset_analysis": "正在分析你的资产配置",
    "liability_analysis": "正在分析你的负债情况",
    "goal_analysis": "正在评估你的财务目标",
    "financial_snapshot": "正在获取你的财务概况",
}


def get_tool_display_name(tool_name: str) -> str:
    return TOOL_DISPLAY_NAMES.get(
        tool_name,
        "财务分析",
    )


def get_tool_running_message(tool_name: str) -> str:
    return TOOL_RUNNING_MESSAGES.get(
        tool_name,
        "正在分析财务数据",
    )
