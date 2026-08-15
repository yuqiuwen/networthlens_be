from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models._mixin import BaseMixin
from app.models.asset import Account


class AccountRepo(BaseMixin[Account]):
    async def list_by_names(
        self,
        session: AsyncSession,
        user_id: int,
        names: set[str],
    ) -> list[Account]:
        """List active accounts whose names exactly match the supplied names."""
        if not names:
            return []

        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.deleted_id == "0",
            Account.name.in_(names),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list(
        self,
        session,
        user_id: int,
        *,
        account_type=None,
        status=None,
        name=None
    ):
        stmt = (
            select(Account)
            .where(
                Account.user_id == user_id,
                Account.deleted_id == "0",
            )
            .order_by(Account.sort_no.asc(), Account.ctime.desc())
        )

        cond = []
        if account_type:
            cond.append(Account.account_type == account_type)

        if status:
            cond.append(Account.status == status)

        if name is not None:
            cond.append(Account.name.ilike(f"%{name}%"))

        ret = await session.execute(stmt)
        return ret.scalars().all()

    async def retrieve(
        self,
        session,
        account_id: str,
        user_id: int,
    ):
        return await self.first_or_404(
            session,
            Account.id == account_id,
            Account.user_id == user_id,
            Account.deleted_id == "0",
        )

    async def exists_name(
        self,
        session,
        user_id: int,
        name: str,
        exclude_id: str | None = None,
    ):
        stmt = select(Account.id).where(
            Account.user_id == user_id,
            Account.name == name,
            Account.deleted_id == "0",
        )

        if exclude_id:
            stmt = stmt.where(Account.id != exclude_id)

        ret = await session.execute(stmt)
        return ret.first() is not None

    async def remove(
        self,
        session,
        account_id: str,
        user_id: int,
    ):
        return await self.query_update(
            session,
            cond=[
                Account.id == account_id,
                Account.user_id == user_id,
                Account.deleted_id == "0",
            ],
            data={
                "deleted_id": account_id,
            },
        )


account_repo = AccountRepo(Account)
