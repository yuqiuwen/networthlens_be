from fastapi import Depends
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import PageRespModel, RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.liability import CreateLiabilitySchema, CreateRepaymentSchema, LiabilityDetailSchema, LiabilityListSchema, LiabilityQuerySchema, RepaymentSchema, UpdateLiabilitySchema
from app.services.liability import LiabilityRepaymentService, LiabilityService


router = BaseAPIRouter(prefix="/liability", tags=["负债管理"])


@router.post(
    "",
    summary="创建负债",
    response_model=RespModel[str],
)
async def create_liability(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateLiabilitySchema,
):
    data = await LiabilityService().create(
        session,
        cur_user,
        data,
    )

    return make_response(data=data)


@router.get(
    "",
    summary="负债列表",
    response_model=PageRespModel[LiabilityListSchema],
)
async def list_liability(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: LiabilityQuerySchema = Depends(),
):
    data = await LiabilityService().list(
        session,
        cur_user,
        query,
    )

    return make_response(data=data)


@router.get(
    "/{liability_id}",
    summary="负债详情",
    response_model=RespModel[LiabilityDetailSchema],
)
async def get_liability(
    liability_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    data = LiabilityService().detail(
            session,
            cur_user,
            liability_id,
        )

    return make_response(data=data)


@router.put(
    "/{liability_id}",
    summary="更新负债",
    response_model=RespModel[bool],
)
async def update_liability(
    liability_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: UpdateLiabilitySchema,
):
    data = LiabilityService().update(
            session,
            cur_user,
            liability_id,
            data,
        )

    return make_response(data=data)


@router.delete(
    "/{liability_id}",
    summary="删除负债",
    response_model=RespModel[bool],
)
async def delete_liability(
    liability_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = LiabilityService().delete(
        session,
        cur_user,
        liability_id,
    )

    return make_response(data=ret)


@router.post(
    "/{liability_id}/repayments",
    summary="新增还款",
    response_model=RespModel[str],
)
async def create_repayment(
    liability_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateRepaymentSchema,
):
    data = LiabilityRepaymentService().create(
            session,
            cur_user,
            liability_id,
            data,
        )
    return make_response(data=data)


@router.get(
    "/{liability_id}/repayments",
    summary="还款记录",
    response_model=RespModel[list[RepaymentSchema]],
)
async def list_repayment(
    liability_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    data = LiabilityRepaymentService().list(
            session,
            cur_user,
            liability_id,
        )

    return make_response(data=data)