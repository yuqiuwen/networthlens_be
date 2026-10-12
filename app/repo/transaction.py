from datetime import date, datetime
from decimal import Decimal
import random
from typing import List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from app.constant import TransactionType
from app.repo.category import category_repo
from sqlalchemy import func, select, case, or_

from app.core.exception import APIException
from app.models._mixin import BaseMixin
from app.models.transaction import Transaction, TransactionCategoryWord, gen_transaction_id
from app.schemas.stats import TrendGranularity
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
        transaction_type: Sequence[TransactionType] | TransactionType | None = None,
        category_id: List[str] = None,
        source_account_id=None,
        target_account_id: List[str] = None,
        keywords: str = None,
        start_time,
        end_time,
    ):
        cond = [
            self.model.user_id == user_id,
            self.model.deleted_id == "0",
        ]

        if transaction_type:
            if isinstance(transaction_type, TransactionType):
                cond.append(self.model.transaction_type == transaction_type)
            else:
                cond.append(self.model.transaction_type.in_(transaction_type))

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
        if keywords:
            cond.append(
                or_(
                    self.model.merchant.ilike(f"%{keywords}%"),
                    self.model.product.ilike(f"%{keywords}%"),
                )
            )

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
            keywords=query.keywords,
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
            }
            for item in records
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
        transaction_type: Sequence[TransactionType] | TransactionType | None = None,
        start_time=None,
        end_time=None,
        category_id: list[str] = None,
        target_account_id: list[str] = None,
        keywords: str = None,
    ):
        cond = self.build_query_cond(
            user_id,
            transaction_type=transaction_type,
            start_time=start_time,
            end_time=end_time,
            category_id=category_id,
            target_account_id=target_account_id,
            keywords=keywords
        )

        stmt = select(
            func.coalesce(
                func.sum(self.model.amount),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)

        return ret.scalar_one()

    async def aggregate_cash_flow(
        self,
        session: AsyncSession,
        user_id: int,
        start: date | datetime,
        end: date | datetime,
        granularity: TrendGranularity,
    ):
        # ----------------------------
        # 1. 时间分桶
        # ----------------------------

        if granularity == TrendGranularity.DAY:
            bucket = func.date(Transaction.occurred_at)

        elif granularity == TrendGranularity.MONTH:
            bucket = func.date_trunc(
                "month",
                Transaction.occurred_at,
            )

        else:
            raise ValueError(f"Unsupported granularity: {granularity}")

        # ----------------------------
        # 2. 收入
        # ----------------------------

        income_expr = case(
            (
                Transaction.transaction_type == TransactionType.INCOME,
                Transaction.amount,
            ),
            else_=Decimal("0"),
        )

        # ----------------------------
        # 3. 支出
        #
        # expense = 正常消费
        # refund  = 冲减消费
        # ----------------------------

        expense_expr = case(
            (
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.amount,
            ),
            else_=Decimal("0"),
        )

        # ----------------------------
        # 4. 查询
        # ----------------------------

        stmt = (
            select(
                bucket.label("bucket"),
                func.coalesce(
                    func.sum(income_expr),
                    0,
                ).label("income"),
                func.coalesce(
                    func.sum(expense_expr),
                    0,
                ).label("expense"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.occurred_at >= start,
                Transaction.occurred_at < end,
                Transaction.transaction_type.in_(
                    [
                        TransactionType.INCOME,
                        TransactionType.EXPENSE,
                    ]
                ),
            )
            .group_by(bucket)
            .order_by(bucket)
        )

        result = await session.execute(stmt)

        return result.all()

    async def agg_expense_category(self, session, user_id, start: date, end: date):
        expense_amount = case(
            (
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.amount,
            ),
            else_=Decimal("0"),
        )

        stmt = (
            select(
                Transaction.category_id,
                func.coalesce(func.sum(expense_amount), 0).label("amount"),
                func.count(
                    case(
                        (
                            Transaction.transaction_type == TransactionType.EXPENSE,
                            Transaction.id,
                        )
                    )
                ).label("transaction_count"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.occurred_at >= start,
                Transaction.occurred_at < end,
                Transaction.transaction_type.in_([TransactionType.EXPENSE]),
            )
            .group_by(
                Transaction.category_id,
            )
        )

        result = await session.execute(stmt)

        return result.all()


class TransactionCategoryWordRepo(BaseMixin[TransactionCategoryWord]):
    async def list(self, session, user_id):
        stmt = self.filter(self.model.user_id == user_id).order_by(
            self.model.priority, self.model.id.desc()
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def add(self, session, user_id, data: dict):
        return await self.create(session, {**data, "user_id": user_id})

    async def edit(self, session, user_id, pk: int, data: dict):
        return await self.query_update(
            session, cond=(self.model.id == pk, self.model.user_id == user_id), data=data
        )

    async def remove(self, session, user_id, data: List[int]):
        return await self.delete(session, self.model.user_id == user_id, self.model.id.in_(data))


transaction_repo = TransactionRepo(Transaction)

transaction_category_word_repo = TransactionCategoryWordRepo(TransactionCategoryWord)
