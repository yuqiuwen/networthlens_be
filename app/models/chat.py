from app.agent.constant import AIChatSessionStatus
from app.models.module import *


class AIChatSession(BaseModel, TimeModel):
    """
    聊天会话

    字段说明：

    - title: 会话标题
    - status: AIChatSessionStatus
    - last_message_at: 最后一条消息时间
    """

    __tablename__ = "ai_chat_session"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(100))
    status = Column(SmallInteger, nullable=False, default=AIChatSessionStatus.NORMAL)
    deleted_id = Column(String(26), nullable=False, default="0",)


class AIChatMessage(BaseModel, TimeModel):
    """
    Chat消息

    字段说明：

    - role: AgentRole

    - content:
        用户输入
        Agent回复
        Tool返回

    - tool_name:
        tool消息时记录工具名

    - token_count:
        本条消息token数

    - model:
        使用模型名称
    """

    __tablename__ = "ai_chat_message"

    __table_args__ = (Index(None, 'session_id', 'user_id', 'deleted_id'),)

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    session_id = Column(String(26), nullable=False)
    role = Column(SmallInteger, nullable=False,)
    content = Column(Text, nullable=False)
    tool_name = Column(String(100))
    token_count = Column(Integer)
    model = Column(String(100))
    extra_info = Column(JSON)
    deleted_id = Column(String(26), nullable=False, default="0")
