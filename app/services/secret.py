import os
from typing import Literal

from app.config import settings
from app.core.exception import APIException
from app.repo.secret import secret_repo


class SecretService:
    @staticmethod
    async def get_status(session, cur_user):
        secret = await secret_repo.get_default(session, cur_user.id)
        return {"configured": secret is not None}

    @staticmethod
    async def set_default(session, cur_user, code: str):
        await secret_repo.set_default(session, cur_user.id, code)
        return True

    @staticmethod
    async def verify_default(session, cur_user, code: str):
        secret = await secret_repo.get_default(session, cur_user.id)
        if secret is None:
            raise APIException("密钥尚未设置", code=404, errmsg="请先在个人中心设置密钥")
        if not secret.secret_valid(code):
            raise APIException("密钥错误", code=400, errmsg="密钥错误")
        return True

    @staticmethod
    async def delete_default(session, cur_user):
        return await secret_repo.delete_default(session, cur_user.id)

    @staticmethod
    async def get_rsa_public_key(biz: Literal["user_pwd"]):
        if biz == "user_pwd":
            ret = os.getenv("PWD_PUBLIC_KEY")
            return {"public_key": ret}
