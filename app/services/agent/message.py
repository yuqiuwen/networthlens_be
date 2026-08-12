from app.agent.constant import AgentRole
from app.repo.chat import chat_message_repo, chat_session_repo
from app.schemas.chat import ChatMessageQuerySchema
from app.utils.common import gen_ulid


class MessageService:
    async def create_user_message(
        self,
        session,
        user_id: int,
        session_id: str,
        content: str,
    ):
        return await chat_message_repo.create(
            session,
            {
                "id": gen_ulid(),
                "session_id": session_id,
                "role": AgentRole.USER,
                "user_id": user_id,
                "content": content,
            },
        )

    async def create_assistant_message(
        self,
        session,
        session_id: str,
        content: str,
        user_id: int,
        token_count: int | None = None,
        model: str | None = None,
        extra_info: dict = None
    ):
        return await chat_message_repo.create(
            session,
            {
                "id": gen_ulid(),
                "session_id": session_id,
                "user_id": user_id,
                "role": AgentRole.ASSISTANT,
                "content": content,
                "token_count": token_count,
                "model": model,
                "extra_info": extra_info
            },
        )

    async def create_tool_message(
        self,
        session,
        session_id: str,
        tool_name: str,
        content: str,
    ):
        return await chat_message_repo.create(
            session,
            {
                "id": gen_ulid(),
                "session_id": session_id,
                "role": AgentRole.TOOL,
                "tool_name": tool_name,
                "content": content,
            },
        )

    async def list(
        self,
        session,
        cur_user,
        params: ChatMessageQuerySchema,

    ):
        return (
            await chat_message_repo.list_by_session(
                session,
                params.session_id,
                cur_user.id,
                params.last,
                params.limit
            )
        )

    async def recent_context(
        self,
        session,
        user_id: int,
        session_id: str,
        limit: int = 20,
    ):
        return (
            await chat_message_repo.latest_messages(
                session,
                user_id,
                session_id,
                limit,
            )
        )

    async def touch_session(
        self,
        session,
        session_id: str,
    ):
        chat_session = (
            await chat_session_repo.get(
                session,
                session_id,
            )
        )

        if not chat_session:
            return

        await chat_session_repo.save(
            session,
            chat_session,
        )