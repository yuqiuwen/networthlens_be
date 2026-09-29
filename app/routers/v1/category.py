from fastapi import Depends
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel
from app.routers import BaseAPIRouter
from app.schemas.category import (
    CategoryQuerySchema,
    CategorySchema,
    CreateCategorySchema,
    UpdateCategorySchema,
)
from app.core.http_handler import make_response
from app.services.category import CategoryService


router = BaseAPIRouter(prefix="/category", tags=["分类管理"])


@router.post("", summary="创建分类", response_model=RespModel[str])
async def create_category(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateCategorySchema,
):
    ret = await CategoryService().create(session, cur_user, data)
    return make_response(data=ret)


@router.get("", summary="分类列表", response_model=RespModel[list[CategorySchema]])
async def list_category(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: CategoryQuerySchema = Depends(),
):
    data = await CategoryService().list(session, cur_user, query)
    return make_response(data=data)


@router.put("/{category_id}", summary="更新分类", response_model=RespModel[bool])
async def update_category(
    category_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: UpdateCategorySchema,
):
    ret = await CategoryService().update(session, cur_user, category_id, data)
    return make_response(data=ret)


@router.delete("/{category_id}", summary="删除分类", response_model=RespModel[bool])
async def delete_category(
    category_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await CategoryService().delete(session, cur_user, category_id)
    return make_response(data=ret)