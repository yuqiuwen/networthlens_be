from fastapi import Depends, UploadFile
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import PageRespModel, RespModel
from app.routers import BaseAPIRouter
from app.schemas.transaction import (
    CreateTransactionSchema,
    ImportTransactionSchema,
    TransactionDetailSchema,
    TransactionListSchema,
    TransactionQuerySchema,
    UpdateTransactionSchema,
)
from app.core.http_handler import make_response
from app.services.transaction import TransactionService


router = BaseAPIRouter(prefix="/transaction", tags=["流水管理"])


@router.post("", summary="创建流水", response_model=RespModel[str])
async def create_transaction(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateTransactionSchema,
):
    data = await TransactionService().create(session, cur_user, data)
    return make_response(data=data)


@router.get("", summary="流水分页", response_model=PageRespModel[TransactionListSchema])
async def list_transaction(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: TransactionQuerySchema = Depends(),
):
    data = await TransactionService().list(session, cur_user, query)
    return make_response(data=data)


@router.get("/{transaction_id}", summary="流水详情", response_model=RespModel[TransactionDetailSchema])
async def get_transaction(
    transaction_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    data = await TransactionService().detail(session, cur_user, transaction_id)
    return make_response(data=data)


@router.put("/{transaction_id}", summary="更新流水", response_model=RespModel[bool])
async def update_transaction(
    transaction_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: UpdateTransactionSchema,
):
    data = await TransactionService().update(session, cur_user, transaction_id)
    return make_response(data=data)


@router.delete("/{transaction_id}", summary="删除流水", response_model=RespModel[bool])
async def delete_transaction(
    transaction_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    data = await TransactionService().delete(session, cur_user, transaction_id)
    return make_response(data=data)


@router.post("/import", summary="导入流水", response_model=RespModel[ImportTransactionSchema])
async def import_transaction(
    file: UploadFile,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    data = await TransactionService().import_excel(session, cur_user, file)

    return make_response(data=data)