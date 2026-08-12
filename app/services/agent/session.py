from app.repo.chat import chat_session_repo
from app.core.exception import APIException
from app.utils.common import gen_ulid


class AgentSessionService:
    async def create(
        self,
        session,
        cur_user,
        title: str | None = None,
    ):
        item = await chat_session_repo.create(
            session,
            {
                "id": gen_ulid(),
                "user_id": cur_user.id,
                "title": title,
            },
        )

        return item

    async def list(
        self,
        session,
        cur_user,
    ):
        return (
            await chat_session_repo.list_by_user(
                session,
                cur_user.id,
            )
        )

    async def detail(
        self,
        session,
        cur_user,
        session_id: str,
    ):
        item = (
            await chat_session_repo.detail(
                session,
                session_id,
                cur_user.id,
            )
        )

        if not item:
            raise APIException(
                errmsg="会话不存在",
                code=404,
            )

        return item

    async def delete(
        self,
        session,
        cur_user,
        session_id: str,
    ):
        item = (
            await chat_session_repo.detail(
                session,
                session_id,
                cur_user.id,
            )
        )

        if not item:
            raise APIException(
                errmsg="会话不存在",
                code=404,
            )

        await chat_session_repo.soft_delete(
            session,
            session_id,
            cur_user.id,
        )

        return True