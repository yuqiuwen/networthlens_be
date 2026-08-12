from fastapi import Depends
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel, PageRespModel
from app.routers import BaseAPIRouter
from app.schemas.asset import (
    AssetDetailSchema,
    AssetListSchema,
    AssetQuerySchema,
    AssetValuationSchema,
    CreateAssetSchema,
    CreateAssetValuationSchema,
    UpdateAssetSchema,
)
from app.core.http_handler import make_response
from app.services.asset import AssetService

router = BaseAPIRouter(prefix="/asset", tags=["资产管理"])


@router.post("", summary="创建资产", response_model=RespModel[str])
async def create_asset(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateAssetSchema,
):
    ret = await AssetService().create(session, cur_user, data)
    return make_response(data=ret)


@router.get("", summary="资产列表", response_model=PageRespModel[AssetListSchema])
async def list_asset(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: AssetQuerySchema = Depends(),
):
    ret = await AssetService().list(session, cur_user, query)
    return make_response(data=ret)


@router.get("/{asset_id}", summary="资产详情", response_model=RespModel[AssetDetailSchema])
async def get_asset(
    asset_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await AssetService().detail(session, cur_user, asset_id)
    return make_response(data=ret)


@router.put("/{asset_id}", summary="更新资产", response_model=RespModel[bool])
async def update_asset(
    asset_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: UpdateAssetSchema,
):
    ret = await AssetService().update(session, cur_user, asset_id, data)
    return make_response(data=ret)


@router.delete("/{asset_id}", summary="删除资产", response_model=RespModel[bool])
async def delete_asset(
    asset_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await AssetService().delete(session, cur_user, asset_id)
    return make_response(data=ret)


@router.post(
    "/{asset_id}/valuations",
    summary="新增资产估值",
    response_model=RespModel[str],
)
async def create_asset_valuation(
    asset_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateAssetValuationSchema,
):
    ret = await AssetService().add_valuation(session, cur_user, asset_id, data)
    return make_response(data=ret)


@router.get(
    "/{asset_id}/valuations",
    summary="资产估值历史",
    response_model=RespModel[list[AssetValuationSchema]],
)
async def list_asset_valuation(
    asset_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await AssetService().valuation_history(session, cur_user, asset_id)
    return make_response(data=ret)