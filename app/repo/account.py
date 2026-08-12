from sqlalchemy import select

from app.models._mixin import BaseMixin
from app.models.asset import Account


class AccountRepo(BaseMixin[Account]):
    async def list(
        self,
        session,
        user_id: int,
        *,
        account_type=None,
        status=None,
    ):
        stmt = (
            select(Account)
            .where(
                Account.user_id == user_id,
                Account.deleted_id == "0",
            )
            .order_by(Account.sort_no.asc(), Account.ctime.desc())
        )

        if account_type:
            stmt = stmt.where(Account.account_type == account_type)

        if status:
            stmt = stmt.where(Account.status == status)

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


