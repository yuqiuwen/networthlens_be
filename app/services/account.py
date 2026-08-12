from fastapi import HTTPException

from app.constant import AccountStatus
from app.core.exception import APIException
from app.models.user import User
from app.repo.account import account_repo
from app.schemas.account import CreateAccountSchema
from app.utils.common import gen_ulid


class AccountService:
    async def create(
        self,
        session,
        cur_user: User,
        data: CreateAccountSchema,
    ):
        exists = await account_repo.exists_name(
            session,
            cur_user.id,
            data.name,
        )

        if exists:
            raise APIException(errmsg="账户名称已存在")

        instance = await account_repo.create(
            session,
            {
                "id": gen_ulid(),
                "user_id": cur_user.id,
                **data.model_dump(),
            },
        )

        return instance.id

    async def list(
        self,
        session,
        cur_user: User,
        account_type=None,
        status=None,
    ):
        return await account_repo.list(
            session,
            cur_user.id,
            account_type=account_type,
            status=status,
        )

    async def detail(
        self,
        session,
        cur_user: User,
        account_id: str,
    ):
        account = await account_repo.retrieve(
            session,
            account_id,
            cur_user.id,
        )

        return account

    async def update(
        self,
        session,
        cur_user: User,
        account_id: str,
        data,
    ):
        account = await account_repo.retrieve(
            session,
            account_id,
            cur_user.id,
        )

        payload = data.model_dump(exclude_unset=True)

        if "name" in payload:
            exists = await account_repo.exists_name(
                session,
                cur_user.id,
                payload["name"],
                exclude_id=account_id,
            )

            if exists:
                raise APIException(errmsg="账户名称已存在")

        await account_repo.update(
            session,
            account,
            payload,
        )

        return True

    async def delete(
        self,
        session,
        cur_user: User,
        account_id: str,
    ):
        account = await account_repo.retrieve(
            session,
            account_id,
            cur_user.id,
        )

        if account.status != AccountStatus.CLOSED:
            raise APIException(errmsg="请先关闭账户")

        await account_repo.remove(
            session,
            account_id,
            cur_user.id,
        )

        return True

