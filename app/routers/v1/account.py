from fastapi import Query

from app.constant import AccountStatus, AccountType
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.account import AccountDetailSchema, AccountListSchema, CreateAccountSchema, UpdateAccountSchema
from app.services.account import AccountService


router = BaseAPIRouter(prefix="/account", tags=["account"])


@router.post("", summary="创建账户", response_model=RespModel[str])
async def create_account(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateAccountSchema,
):
    ret = await AccountService().create(session, cur_user, data)
    return make_response(data=ret)


@router.get("", summary="账户列表", response_model=RespModel[list[AccountListSchema]])
async def list_account(
    session: SessionDep,
    cur_user: RequireAuthDep,
    account_type: AccountType = Query(None),
    status: AccountStatus = Query(None)
):
    ret = await AccountService().list(session, cur_user, account_type, status)
    return make_response(data=ret)


@router.get("/{account_id}", summary="账户详情", response_model=RespModel[AccountDetailSchema])
async def get_account(
    account_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await AccountService().detail(session, cur_user, account_id)
    return make_response(data=ret)


@router.put("/{account_id}", summary="更新账户", response_model=RespModel[bool])
async def update_account(
    account_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: UpdateAccountSchema,
):
    ret = await AccountService().update(session, cur_user, account_id, data)
    return make_response(data=ret)


@router.delete("/{account_id}", summary="删除账户", response_model=RespModel[bool])
async def delete_account(
    account_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await AccountService().delete(session, cur_user, account_id)
    return make_response(data=ret)