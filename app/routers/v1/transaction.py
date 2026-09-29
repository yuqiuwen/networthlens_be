from datetime import datetime
import keyword
from typing import List, Literal
from fastapi import Depends, UploadFile
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import PageRespModel, RespModel
from app.constant import TransactionType
from app.routers import BaseAPIRouter
from app.schemas.transaction import (
    CreateTransCategoryWordSchema,
    CreateTransactionSchema,
    ImportTransactionSchema,
    TransCategoryWordItem,
    TransactionDetailSchema,
    TransactionListSchema,
    TransactionQuerySchema,
    TransactionSummarySchema,
    UpdateTransactionSchema,
)
from app.core.http_handler import make_response
from app.services.transaction import TransactionService


router = BaseAPIRouter(prefix="/transaction", tags=["流水管理"])


@router.post("/category_word", summary="创建分类匹配词")
async def create_category_word(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateTransCategoryWordSchema
):
    data = await TransactionService().create_trans_category_word(
        session,
        cur_user.id,
        data,
    )

    return make_response(data=data)


@router.put("/category_word/{pk}", summary="修改分类匹配词")
async def update_category_word(
    pk: int,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateTransCategoryWordSchema
):
    data = await TransactionService().update_trans_category_word(
        session,
        cur_user.id,
        pk,
        data.words,
    )

    return make_response(data=data)


@router.get("/category_word", summary="获取分类匹配词", response_model=RespModel[List[TransCategoryWordItem]])
async def list_category_word(
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    data = await TransactionService().list_trans_category_word(
        session,
        cur_user.id,
    )

    return make_response(data=data)



@router.delete("/category_word", summary="删除分类匹配词")
async def delete_category_word(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: List[int]
):
    data = await TransactionService().delete_trans_category_word(
        session,
        cur_user.id,
        data,
    )

    return make_response(data=data)



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


@router.get("/summary", summary="流水汇总", response_model=RespModel[TransactionSummarySchema])
async def summarize_transaction(
    session: SessionDep,
    cur_user: RequireAuthDep,
    transaction_type: TransactionType | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    category_id: str | None = None,
    target_account_id: str | None = None,
    keywords: str | None = None,
):
    if category_id:
        category_id = [str(x.strip()) for x in category_id.split(",")]
    if target_account_id:
        target_account_id = [str(x.strip()) for x in target_account_id.split(",")]

    data = await TransactionService().summary(
        session,
        cur_user,
        transaction_type=transaction_type,
        start_time=start_time,
        end_time=end_time,
        category_id=category_id,
        target_account_id=target_account_id,
        keywords=keywords
    )
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
    data = await TransactionService().update(session, cur_user, transaction_id, data)
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
    import_source: Literal["wx", "alipay"],
    file: UploadFile,
    session: SessionDep,
    cur_user: RequireAuthDep,
    account_id: str | None = None,
):
    data = await TransactionService().import_excel(
        session,
        cur_user,
        import_source,
        file,
        account_id,
    )

    return make_response(data=data)


