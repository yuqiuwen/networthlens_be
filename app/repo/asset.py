from sqlalchemy import func, select

from app.models.asset import Asset
from app.models._mixin import BaseMixin
from app.utils.paginator import PaginatedResponse, Paginator


class AssetRepo(BaseMixin[Asset]):
    async def list_page(
        self,
        session,
        user_id: int,
        *,
        asset_type=None,
        status=None,
        page=1,
        limit=100,
    ) -> PaginatedResponse:
        cond = [
            Asset.user_id == user_id,
            Asset.deleted_id == "0",
        ]
        

        if asset_type:
            cond.append(Asset.asset_type == asset_type)
        if status:
            cond.append(Asset.status == status)

        stmt = self.filter(*cond).order_by(self.model.id.desc())
        paged = await Paginator(session).paginate(stmt, page, limit)
        
        return paged

    async def get_detail(
        self,
        session,
        asset_id: str,
        user_id: int,
    ):
        return await self.filter_one(
            session,
            Asset.id == asset_id,
            Asset.user_id == user_id,
            Asset.deleted_id == "0",
        )

    async def soft_delete(
        self,
        session,
        asset_id: str,
        user_id: int,
    ):
        return await self.query_update(
            session,
            cond=[
                Asset.id == asset_id,
                Asset.user_id == user_id,
                Asset.deleted_id == "0",
            ],
            data={
                "deleted_id": asset_id,
            },
        )

    async def asset_summary(
        self,
        session,
        user_id: int,
    ):
        stmt = select(
            func.coalesce(
                func.sum(
                    Asset.current_value
                ),
                0,
            )
        ).where(
            Asset.user_id == user_id,
            Asset.deleted_id == "0",
        )

        ret = await session.execute(stmt)
        return ret.scalar_one()


asset_repo = AssetRepo(Asset)