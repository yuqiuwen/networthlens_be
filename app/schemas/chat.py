from datetime import datetime
from pydantic import BaseModel, Field

from app.agent.constant import AgentRole, AIChatSessionStatus, ChatEventType
from app.schemas.common import CursorPageQueryModel, EntityModel


class AIChatSessionSchema(EntityModel):
    id: str
    title: str | None
    status: AIChatSessionStatus
    ctime: datetime


class AIChatMessageSchema(EntityModel):
    id: str
    role: AgentRole
    content: str
    tool_name: str | None
    token_count: int | None
    model: str | None
    ctime: datetime


class ChatReqSchema(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=10000)


class ChatRespSchema(BaseModel):
    session_id: str
    message_id: str
    answer: str


class CreateChatSessionSchema(BaseModel):
    """
    创建会话
    """

    title: str | None = Field(default=None, max_length=100)


class UpdateChatSessionSchema(BaseModel):
    """
    修改会话
    """

    title: str = Field(min_length=1, max_length=100)


class ChatStreamEvent(BaseModel):
    type: ChatEventType

    data: dict


class ChatMessageQuerySchema(CursorPageQueryModel):
    session_id: str
