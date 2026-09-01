from datetime import date
from typing import Sequence
from app.constant import AssetStatus
from sqlalchemy import func, select

from app.models.asset import Asset, WealthSnapshot
from app.models._mixin import BaseMixin
from app.schemas.stats import DateRange, TrendGranularity
from app.utils.paginator import PaginatedResponse, Paginator


class AssetRepo(BaseMixin[Asset]):
    async def list_page(
        self,
        session,
        user_id: int,
        *,
        asset_type=None,
        category_ids=None,
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
        if category_ids:
            cond.append(Asset.category_id.in_(category_ids))

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
        status: Sequence[AssetStatus] | AssetStatus = None,
        purchase_date_start: date = None,
        purchase_date_end: date = None,
    ):
        cond = [
            Asset.user_id == user_id,
            Asset.deleted_id == "0",
        ]
        if status is not None:
            if isinstance(status, Sequence):
                cond.append(Asset.status.in_(status))
            else:
                cond.append(Asset.status == status)

        if purchase_date_start:
            cond.append(Asset.purchase_date >= purchase_date_start)
        if purchase_date_end:
            cond.append(Asset.purchase_date < purchase_date_end)


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


    async def get_asset_category_stats(self, session, user_id):
        stmt = select(
            self.model.category_id,
            func.sum(self.model.current_value).label("current_value"),
            func.count(self.model.id).label("asset_count")
        ).where(
            self.model.user_id == user_id,
            self.model.deleted_id == "0"
        ).group_by(
            self.model.category_id
        )

        result = await session.execute(stmt)

        return result.all()


class WealthSnapshotRepo(BaseMixin[WealthSnapshot]):
    async def retrieve(self, session, user_id, snapshot_date: date) -> WealthSnapshot:
        return await self.filter_one(
            session,
            self.model.user_id == user_id,
            self.model.snapshot_date == snapshot_date,
        )

    async def agg_wealth_flow(self, session, user_id, granularity: TrendGranularity, start: date, end: date):
        if granularity == TrendGranularity.DAY:
            bucket = func.date(self.model.snapshot_date)

        elif granularity == TrendGranularity.MONTH:
            bucket = func.date_trunc(
                "month",
                self.model.snapshot_date,
            )

        else:
            raise ValueError(f"Unsupported granularity: {granularity}")


        stmt = (
            select(
                bucket.label("bucket"),
                func.coalesce(
                    func.sum(self.model.account_value),
                    0,
                ).label("account_value"),
                func.coalesce(
                    func.sum(self.model.asset_value),
                    0,
                ).label("asset_value"),
                func.coalesce(
                    func.sum(self.model.total_assets),
                    0,
                ).label("total_assets"),
            )
            .where(
                self.model.user_id == user_id,
                self.model.snapshot_date >= start,
                self.model.snapshot_date < end,
            )
            .group_by(bucket)
            .order_by(bucket)
        )

        result = await session.execute(stmt)

        return result.all()


asset_repo = AssetRepo(Asset)
wealth_snapshot_repo = WealthSnapshotRepo(WealthSnapshot)