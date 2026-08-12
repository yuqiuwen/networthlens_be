from sqlalchemy import func, select
from app.models._mixin import BaseMixin
from app.models.asset import Liability, LiabilityRepayment
from app.utils.paginator import Paginator


class LiabilityRepo(BaseMixin[Liability]):
    async def list_page(
        self,
        session,
        user_id: int,
        *,
        liability_type=None,
        status=None,
        page=1,
        limit=20,
    ):
        cond = [
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]
        
        if liability_type:
            cond.append(self.model.liability_type == liability_type)

        if status:
            cond.append(self.model.status == status)

        stmt = self.filter(*cond).order_by(self.model.id.desc)
        paged = Paginator(session).paginate(stmt, page, limit)

        return paged

    async def get_detail(
        self,
        session,
        liability_id: str,
        user_id: int,
    ):
        return await self.filter_one(
            session,
            Liability.id == liability_id,
            Liability.user_id == user_id,
            Liability.deleted_id == "0",
        )

    async def soft_delete(
        self,
        session,
        liability_id: str,
        user_id: int,
    ):
        return await self.query_update(
            session,
            cond=[
                Liability.id == liability_id,
                Liability.user_id == user_id,
                Liability.deleted_id == "0",
            ],
            data={
                "deleted_id": liability_id,
            },
        )

    async def total_remaining_principal(
        self,
        session,
        user_id: int,
    ):
        stmt = select(
            func.coalesce(
                func.sum(
                    Liability.remaining_principal
                ),
                0,
            )
        ).where(
            Liability.user_id == user_id,
            Liability.deleted_id == "0",
        )

        return (
            await session.execute(stmt)
        ).scalar_one()



class LiabilityRepaymentRepo(
    BaseMixin[LiabilityRepayment]
):
    async def list_by_liability(
        self,
        session,
        liability_id: str,
    ):
        stmt = (
            select(
                LiabilityRepayment
            )
            .where(
                LiabilityRepayment.liability_id
                == liability_id
            )
            .order_by(
                LiabilityRepayment.paid_at.desc()
            )
        )

        ret = await session.execute(stmt)

        return ret.scalars().all()


    async def count_by_liability(
        self,
        session,
        liability_id: str,
    ):
        stmt = (
            select(func.count())
            .select_from(
                LiabilityRepayment
            )
            .where(
                LiabilityRepayment.liability_id
                == liability_id
            )
        )

        return (
            await session.execute(stmt)
        ).scalar_one()


liability_repo = LiabilityRepo(Liability)
liability_repayment_repo = LiabilityRepaymentRepo(LiabilityRepayment)
