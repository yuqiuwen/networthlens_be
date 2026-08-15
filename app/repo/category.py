from sqlalchemy import select

from app.models.asset import Category
from app.models._mixin import BaseMixin


class CategoryRepo(BaseMixin[Category]):
    async def list_by_user(
        self,
        session,
        user_id: int,
        *,
        category_type=None,
        ids=None
    ):
        cond = [
            Category.deleted_id == "0", 
            (Category.user_id == user_id) | (Category.user_id.is_(None))
        ]
        

        if category_type:
            cond.append(Category.category_type == category_type)
        if ids:
            cond.append(Category.id.in_(ids))
            
        stmt = self.filter(
            *cond
        ).order_by(
            Category.sort_no.asc(),
            Category.ctime.asc(),
        )

        ret = await session.execute(stmt)
        return ret.scalars().all()

    async def get_detail(
        self,
        session,
        category_id: str,
        user_id: int,
    ):
        return await self.filter_one(
            session,
            Category.id == category_id,
            Category.deleted_id == "0",
            ((Category.user_id == user_id) | (Category.user_id.is_(None))),
        )

    async def exists_name(
        self,
        session,
        user_id: int,
        category_type: int,
        name: str,
        exclude_id: str | None = None,
    ):
        stmt = select(Category.id).where(
            Category.user_id == user_id,
            Category.category_type == category_type,
            Category.name == name,
            Category.deleted_id == "0",
        )

        if exclude_id:
            stmt = stmt.where(Category.id != exclude_id)

        ret = await session.execute(stmt)
        return ret.first() is not None

    async def exists_code(
        self,
        session,
        user_id: int,
        code: str,
        exclude_id: str | None = None,
    ):
        stmt = select(Category.id).where(
            Category.user_id == user_id,
            Category.code == code,
            Category.deleted_id == "0",
        )

        if exclude_id:
            stmt = stmt.where(Category.id != exclude_id)

        ret = await session.execute(stmt)
        return ret.first() is not None

    async def count_children(
        self,
        session,
        category_id: str,
    ):
        stmt = select(Category.id).where(
            Category.parent_id == category_id,
            Category.deleted_id == "0",
        )

        ret = await session.execute(stmt)
        return len(ret.scalars().all())

    async def soft_delete(
        self,
        session,
        category_id: str,
    ):
        return await self.query_update(
            session,
            cond=[
                Category.id == category_id,
                Category.deleted_id == "0",
            ],
            data={
                "deleted_id": category_id,
            },
        )


category_repo = CategoryRepo(Category)
