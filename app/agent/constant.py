from app.constant import IntEnumPro


class AgentRole(IntEnumPro):
    USER = 1, "用户"
    ASSISTANT = 2, "助手"
    TOOL = 3, "工具"
    SYSTEM = 4, "系统"


class AIChatSessionStatus(IntEnumPro):
    NORMAL = 1, "正常"
    ARCHIVED = 2, "归档"


class ChatEventType(IntEnumPro):
    START = 1, "开始"
    STATUS = 2, "状态"
    TOOL_CALL = 3, "工具调用"
    TOOL_RESULT = 4, "工具结果"
    CONTENT = 5, "内容"
    FINISH = 6, "结束"
    ERROR = 7, "异常"
    THINKING = 8, "思考"