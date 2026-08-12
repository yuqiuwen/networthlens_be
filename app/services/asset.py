
from app.core.exception import APIException
from app.schemas.asset import AssetQuerySchema, CreateAssetSchema, CreateAssetValuationSchema
from app.utils.common import gen_ulid
from app.utils.paginator import PaginatedResponse
from app.repo.asset import asset_repo
from app.repo.asset_valuation import (
    asset_valuation_repo,
)


class AssetService:
    async def create(
        self,
        session,
        cur_user,
        data: CreateAssetSchema,
    ):
        asset = await asset_repo.create(
            session,
            {
                "id": gen_ulid(),
                "user_id": cur_user.id,
                **data.model_dump(),
            },
        )

        return asset.id

    async def list(
        self,
        session,
        cur_user,
        query: AssetQuerySchema,
    ):
        paged = await asset_repo.list_page(
            session,
            cur_user.id,
            asset_type=query.asset_type,
            status=query.status,
            page=query.page,
            limit=query.limit,
        )

        return paged

    async def detail(
        self,
        session,
        cur_user,
        asset_id: str,
    ):
        asset = await asset_repo.get_detail(
            session,
            asset_id,
            cur_user.id,
        )

        if not asset:
            raise APIException(code=404, errmsg="资产不存在")

        return asset

    async def update(
        self,
        session,
        cur_user,
        asset_id: str,
        data,
    ):
        asset = await asset_repo.get_detail(
            session,
            asset_id,
            cur_user.id,
        )

        if not asset:
            raise APIException(code=404, errmsg="资产不存在")

        await asset_repo.update(
            session,
            asset,
            data.model_dump(
                exclude_unset=True
            ),
        )

        return True

    async def delete(
        self,
        session,
        cur_user,
        asset_id: str,
    ):
        asset = await asset_repo.get_detail(
            session,
            asset_id,
            cur_user.id,
        )

        if not asset:
            raise APIException(code=404, errmsg="资产不存在")

        await asset_repo.soft_delete(
            session,
            asset_id,
            cur_user.id,
        )

        return True

    async def add_valuation(
        self,
        session,
        cur_user,
        asset_id: str,
        data: CreateAssetValuationSchema,
    ):
        asset = await asset_repo.get_detail(
            session,
            asset_id,
            cur_user.id,
        )

        if not asset:
            raise APIException(code=404, errmsg="资产不存在")

        valuation = (
            await asset_valuation_repo.create(
                session,
                {
                    "id": gen_ulid(),
                    "asset_id": asset_id,
                    **data.model_dump(),
                },
            )
        )

        return valuation.id

    async def valuation_history(
        self,
        session,
        cur_user,
        asset_id: str,
    ):
        asset = await asset_repo.get_detail(
            session,
            asset_id,
            cur_user.id,
        )

        if not asset:
            raise APIException(code=404, errmsg="资产不存在")

        return await asset_valuation_repo.list_history(
            session,
            asset_id,
        )

    async def summary(
        self,
        session,
        cur_user,
    ):
        total_asset = (
            await asset_repo.asset_summary(
                session,
                cur_user.id,
            )
        )

        return {
            "total_asset": total_asset,
        }
