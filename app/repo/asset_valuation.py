from sqlalchemy import select

from app.models.asset import AssetValuationHistory
from app.models._mixin import BaseMixin


class AssetValuationRepo(
    BaseMixin[AssetValuationHistory]
):
    async def list_history(
        self,
        session,
        asset_id: str,
    ):
        stmt = (
            select(
                AssetValuationHistory
            )
            .where(
                AssetValuationHistory.asset_id
                == asset_id
            )
            .order_by(
                AssetValuationHistory.valuation_date.desc()
            )
        )

        ret = await session.execute(stmt)

        return ret.scalars().all()


asset_valuation_repo = AssetValuationRepo(
    AssetValuationHistory
)   