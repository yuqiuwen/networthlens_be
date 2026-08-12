from app.models._mixin import BaseMixin
from app.models.chat import AIChatMessage, AIChatSession
from app.utils.paginator import ScrollPaginator


class AIChatSessionRepo(
    BaseMixin[AIChatSession]
):
    async def list_by_user(
        self,
        session,
        user_id: int,
    ):
        cond = [
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        stmt = self.filter(*cond).order_by(self.model.id.desc())

        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def detail(
        self,
        session,
        session_id: str,
        user_id: int,
    ):
        cond = [
            self.model.id == session_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        return await self.filter_one(
            session,
            *cond,
        )

    async def soft_delete(
        self,
        session,
        session_id: str,
        user_id: int,
    ):
        cond = [
            self.model.id == session_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        return await self.query_update(
            session,
            cond=cond,
            data={
                "deleted_id": session_id,
            },
        )



class AIChatMessageRepo(
    BaseMixin[AIChatMessage]
):
    async def list_by_session(
        self,
        session,
        session_id: str,
        user_id: int,
        last: str = 0,
        limit: int = 100,
    ):
        cond = [
            self.model.session_id == session_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        stmt = self.filter(*cond).order_by(self.model.id.asc())

        paged = await ScrollPaginator(session, stmt, self.model).paginate(last, limit)
        
        return paged

    async def latest_messages(
        self,
        session,
        user_id: int,
        session_id: str,
        limit: int = 20,
    ):
        cond = [
            self.model.session_id == session_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        stmt = self.filter(*cond).order_by(self.model.id.desc()).limit(limit)

        ret = await session.execute(stmt)

        return list(reversed(ret.scalars().all()))



chat_session_repo = AIChatSessionRepo(AIChatSession)
chat_message_repo = AIChatMessageRepo(AIChatMessage)

