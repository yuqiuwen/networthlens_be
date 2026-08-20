import random
from typing import List
from app.repo.category import category_repo
from sqlalchemy import func, select

from app.core.exception import APIException
from app.models._mixin import BaseMixin
from app.models.transaction import Transaction, gen_transaction_id
from app.schemas.transaction import CreateTransactionSchema, TransactionQuerySchema
from app.utils.common import gen_ulid
from app.utils.dater import DT
from app.utils.paginator import Paginator


class TransactionRepo(BaseMixin[Transaction]):
    """
    流水仓储层
    """

    def build_transaction_uuid(self, user_id: int, version="1"):
        return f"{DT.now_str('%Y%m%d%H%M%S')}{version}{user_id:-4}{random.randint(0, 99):02d}"

    def build_query_cond(
        self,
        user_id: int,
        *,
        transaction_type=None,
        category_id: List[str] =None,
        source_account_id=None,
        target_account_id: List[str]=None,
        start_time,
        end_time,
    ):
        cond = [
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        if transaction_type:
            cond.append(self.model.transaction_type == transaction_type)

        if category_id:
            if len(category_id) == 1:
                cond.append(self.model.category_id == category_id[0])
            else:
                cond.append(self.model.category_id.in_(category_id))

        if source_account_id:
            cond.append(self.model.source_account_id == source_account_id)

        if target_account_id:
            if len(target_account_id) == 1:
                cond.append(self.model.target_account_id == target_account_id[0])
            else:
                cond.append(self.model.target_account_id.in_(target_account_id))

        if start_time:
            cond.append(self.model.occurred_at >= start_time)

        if end_time:
            cond.append(self.model.occurred_at <= end_time)

        return cond

    async def add(self, session, cur_user, data: CreateTransactionSchema):
        transaction_id = data.transaction_id
        if transaction_id:
            exists = await self.exists_external_id(
                session,
                transaction_id,
                cur_user.id,
            )

            if exists:
                raise APIException(
                    "流水号已存在",
                    code=400,
                )

        internal_id = self.build_transaction_uuid(cur_user.id)
        payload = data.model_dump()
        payload["transaction_id"] = transaction_id or f"manual:{internal_id}"
        transaction = await self.create(
            session,
            {
                "id": internal_id,
                "user_id": cur_user.id,
                **payload,
            },
        )

        return transaction.id

    async def page(
        self,
        session,
        user_id: int,
        query: TransactionQuerySchema,
    ):
        category_id = target_account_id = None
        if query.category_id:
            category_id = [str(x.strip()) for x in query.category_id.split(",")]
        if query.target_account_id:
            target_account_id = [str(x.strip()) for x in query.target_account_id.split(",")]

        cond = self.build_query_cond(
            user_id,
            transaction_type=query.transaction_type,
            category_id=category_id,
            source_account_id=query.source_account_id,
            target_account_id=target_account_id,
            start_time=query.start_time,
            end_time=query.end_time,
        )

        stmt = select(self.model).where(*cond).order_by(self.model.occurred_at.desc())

        paged = await Paginator(session).paginate(stmt, query.page, query.limit)

        return paged

    async def detail(
        self,
        session,
        transaction_id: str,
        user_id: int,
    ):
        cond = [
            self.model.id == transaction_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        return await self.filter_one(
            session,
            *cond,
        )

    async def exists_external_id(
        self,
        session,
        external_id: str,
        user_id: int,
    ):
        if not external_id:
            return False

        cond = [
            self.model.transaction_id == external_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        ret = await self.filter_one(session, *cond)

        return ret is not None

    async def list_existing_external_ids(
        self,
        session,
        external_ids: list[str],
    ) -> set[str]:
        """Return external transaction IDs that already exist in the database."""
        if not external_ids:
            return set()

        stmt = select(self.model.transaction_id).where(self.model.transaction_id.in_(external_ids))
        ret = await session.execute(stmt)
        return set(ret.scalars().all())

    async def import_records(self, session, user_id: int, records: list[dict]) -> int:
        """Insert imported records while ignoring concurrent duplicate transaction IDs."""
        if not records:
            return 0
        
        data = [
            {
                "id": gen_ulid(),
                "user_id": user_id,
                **item,
            } for item in records
        ]
        return await self.insert_do_update(
            session,
            data,
            index_elements=["channel", "transaction_id"],
        )
      

    async def soft_delete(
        self,
        session,
        transaction_id: str,
        user_id: int,
    ):
        cond = [
            self.model.id == transaction_id,
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        return await self.query_update(
            session,
            cond=cond,
            data={
                "deleted_id": transaction_id,
            },
        )

    async def sum_amount(
        self,
        session,
        user_id: int,
        *,
        transaction_type=None,
        start_time=None,
        end_time=None,
        category_id: list[str] =None,
        target_account_id: list[str]=None,
    ):
        cond = [
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        if transaction_type:
            cond.append(self.model.transaction_type == transaction_type)

        if start_time:
            cond.append(self.model.occurred_at >= start_time)

        if end_time:
            cond.append(self.model.occurred_at <= end_time)

        if category_id:
            if len(category_id) == 1:
                cond.append(self.model.category_id == category_id[0])
            else:
                cond.append(self.model.category_id.in_(category_id))
        
        if target_account_id:
            if len(target_account_id) > 1:
                cond.append(self.model.target_account_id.in_(target_account_id))
            else:
                cond.append(self.model.target_account_id == target_account_id[0])

        stmt = select(
            func.coalesce(
                func.sum(self.model.amount),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)

        return ret.scalar_one()



transaction_repo = TransactionRepo(Transaction)
