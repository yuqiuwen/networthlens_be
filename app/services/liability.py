from app.constant import LiabilityStatus
from app.schemas.liability import CreateLiabilitySchema, CreateRepaymentSchema, LiabilityQuerySchema, UpdateLiabilitySchema
from app.utils.common import gen_ulid
from app.core.exception import APIException
from app.utils.paginator import PaginatedResponse
from app.repo.liability import liability_repo, liability_repayment_repo


class LiabilityService:
    async def create(
        self,
        session,
        cur_user,
        data: CreateLiabilitySchema,
    ):
        liability = await liability_repo.create(
            session,
            {
                "id": gen_ulid(),
                "user_id": cur_user.id,
                **data.model_dump(),
            },
        )

        return liability.id

    async def list(
        self,
        session,
        cur_user,
        query: LiabilityQuerySchema,
    ):
        paged = await liability_repo.list_page(
                session,
                cur_user.id,
                liability_type=query.liability_type,
                status=query.status,
                page=query.page,
                limit=query.limit,
            )
        

        return paged

    async def detail(
        self,
        session,
        cur_user,
        liability_id: str,
    ):
        liability = (
            await liability_repo.get_detail(
                session,
                liability_id,
                cur_user.id,
            )
        )

        if not liability:
            raise APIException(code=404, errmsg="负债不存在")

        return liability

    async def update(
        self,
        session,
        cur_user,
        liability_id: str,
        data: UpdateLiabilitySchema,
    ):
        liability = (
            await liability_repo.get_detail(
                session,
                liability_id,
                cur_user.id,
            )
        )

        if not liability:
            raise APIException(code=404, errmsg="负债不存在")

        await liability_repo.update(
            session,
            liability,
            data.model_dump(
                exclude_unset=True
            ),
        )

        return True

    async def delete(
        self,
        session,
        cur_user,
        liability_id: str,
    ):
        liability = (
            await liability_repo.get_detail(
                session,
                liability_id,
                cur_user.id,
            )
        )

        if not liability:
            raise APIException(code=404, errmsg="负债不存在")

        await liability_repo.soft_delete(
            session,
            liability_id,
            cur_user.id,
        )

        return True

    async def summary(
        self,
        session,
        cur_user,
    ):
        total_liability = (
            await liability_repo.total_remaining_principal(
                session,
                cur_user.id,
            )
        )

        return {
            "total_liability": total_liability,
        }



class LiabilityRepaymentService:

    async def create(
        self,
        session,
        cur_user,
        liability_id: str,
        data: CreateRepaymentSchema,
    ):
        liability = (
            await liability_repo.get_detail(
                session,
                liability_id,
                cur_user.id,
            )
        )

        if not liability:
            raise APIException(code=404, errmsg="负债不存在")
        if liability.status == LiabilityStatus.SETTLED:
            raise APIException(errmsg="负债已结清")
        if data.principal <= 0:
            raise APIException(errmsg="本金必须大于0")


        if (
            data.principal
            > liability.remaining_principal
        ):
            raise APIException(errmsg="本金超过剩余本金")

        remaining_principal = (
            liability.remaining_principal
            - data.principal
        )

        status = liability.status

        if remaining_principal == 0:
            status = LiabilityStatus.SETTLED

        repayment = await liability_repayment_repo.create(
            session,
            {
                "id": gen_ulid(),
                "liability_id": liability_id,
                **data.model_dump(),
                "remaining_principal": remaining_principal,
            },
            commit=False,
        )

        await liability_repo.update(
            session,
            liability,
            {
                "remaining_principal": remaining_principal,
                "status": status,
            },
            commit=False,
        )

        await session.commit()

        return repayment.id

    async def list(
        self,
        session,
        cur_user,
        liability_id: str,
    ):
        liability = (
            await liability_repo.get_detail(
                session,
                liability_id,
                cur_user.id,
            )
        )

        if not liability:
            raise APIException(code=404, errmsg="负债不存在")

        return await liability_repayment_repo.list_by_liability(
            session,
            liability_id,
        )