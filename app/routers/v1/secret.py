from app.core.http_handler import make_response
from app.core.dependencies import RequireAuthDep, SessionDep
from app.routers import BaseAPIRouter
from app.core.http_handler import RespModel
from app.schemas.sys import (
    EncryptedSecretCodeSchema,
    QSecretSchema,
    SecretCodeSchema,
    SecretStatusSchema,
)
from app.services.secret import SecretService


router = BaseAPIRouter(prefix="/secret", tags=["secret"])


@router.get("", summary="查看默认密钥状态", response_model=RespModel[SecretStatusSchema])
async def get_secret_status(session: SessionDep, cur_user: RequireAuthDep):
    data = await SecretService.get_status(session, cur_user)
    return make_response(data=data)


@router.post("", summary="设置默认查看密钥", response_model=RespModel[bool])
async def set_secret(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: SecretCodeSchema,
):
    ret = await SecretService.set_default(session, cur_user, data.code)
    return make_response(data=ret)


@router.post("/verify", summary="验证默认查看密钥", response_model=RespModel[bool])
async def verify_secret(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: EncryptedSecretCodeSchema,
):
    ret = await SecretService.verify_default(session, cur_user, data.code)
    return make_response(data=ret)


@router.delete("", summary="删除默认查看密钥", response_model=RespModel[bool])
async def delete_secret(session: SessionDep, cur_user: RequireAuthDep):
    ret = await SecretService.delete_default(session, cur_user)
    return make_response(data=ret)


@router.post("/rsa_public_key", summary="获取公钥")
async def get_data(params: QSecretSchema):
    data = await SecretService.get_rsa_public_key(params.biz)
    return make_response(data=data)
