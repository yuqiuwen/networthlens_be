from datetime import datetime
from typing import List

from sqlalchemy import func
from sqlalchemy import select

from app.constant import (
    LiabilityStatus,
    TransactionType,
)
from app.models.asset import (
    Asset,
    Category,
    Goal,
    Liability,
)
from app.models.transaction import Transaction


class FinancialAnalysisRepo:
    """
    财务分析查询仓储

    只负责统计分析类查询

    不负责CRUD
    """

    # ==========================
    # Transaction
    # ==========================

    async def query_transactions(
        self,
        session,
        user_id: int,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        transaction_types: list[int] | None = None,
        category_ids: list[str] | None = None,
        source_account_ids: list[str] | None = None,
        target_account_ids: list[str] | None = None,
    ):
        cond = [
            Transaction.user_id == user_id,
            Transaction.deleted_id == "0",
        ]

        if start_time:
            cond.append(
                Transaction.occurred_at >= start_time
            )

        if end_time:
            cond.append(
                Transaction.occurred_at <= end_time
            )

        if transaction_types:
            cond.append(
                Transaction.transaction_type.in_(
                    transaction_types
                )
            )

        if category_ids:
            cond.append(
                Transaction.category_id.in_(
                    category_ids
                )
            )

        if source_account_ids:
            cond.append(
                Transaction.source_account_id.in_(
                    source_account_ids
                )
            )

        if target_account_ids:
            cond.append(
                Transaction.target_account_id.in_(
                    target_account_ids
                )
            )

        stmt = (
            select(Transaction)
            .where(*cond)
            .order_by(
                Transaction.occurred_at.desc()
            )
        )

        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def sum_transaction_amount(
        self,
        session,
        user_id: int,
        *,
        transaction_type: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        cond = [
            Transaction.user_id == user_id,
            Transaction.deleted_id == "0",
            Transaction.transaction_type
            == transaction_type,
        ]

        if start_time:
            cond.append(
                Transaction.occurred_at >= start_time
            )

        if end_time:
            cond.append(
                Transaction.occurred_at <= end_time
            )

        stmt = select(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)
        
        return ret.scalar_one()

    async def expense_by_category(
        self,
        session,
        user_id: int,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        cond = [
            Transaction.user_id == user_id,
            Transaction.deleted_id == "0",
            Transaction.transaction_type
            == TransactionType.EXPENSE,
        ]

        if start_time:
            cond.append(
                Transaction.occurred_at >= start_time
            )

        if end_time:
            cond.append(
                Transaction.occurred_at <= end_time
            )

        stmt = (
            select(
                Transaction.category_id,
                Category.name,
                func.sum(
                    Transaction.amount
                ).label("amount"),
            )
            .outerjoin(
                Category,
                Category.id
                == Transaction.category_id,
            )
            .where(*cond)
            .group_by(
                Transaction.category_id,
                Category.name,
            )
            .order_by(
                func.sum(
                    Transaction.amount
                ).desc()
            )
        )

        ret = await session.execute(stmt)

        return ret.all()

    # ==========================
    # Asset
    # ==========================

    async def query_assets(
        self,
        session,
        user_id: int,
        *,
        asset_types: list[int] | None = None,
    ) -> List[Asset]:
        cond = [
            Asset.user_id == user_id,
            Asset.deleted_id == "0",
        ]

        if asset_types:
            cond.append(
                Asset.asset_type.in_(
                    asset_types
                )
            )

        stmt = (
            select(Asset)
            .where(*cond)
            .order_by(
                Asset.current_value.desc()
            )
        )

        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def total_asset(
        self,
        session,
        user_id: int,
    ):
        cond = [
            Asset.user_id == user_id,
            Asset.deleted_id == "0",
        ]

        stmt = select(
            func.coalesce(
                func.sum(
                    Asset.current_value
                ),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)

        return ret.scalar_one()

    # ==========================
    # Liability
    # ==========================

    async def query_liabilities(
        self,
        session,
        user_id: int,
        *,
        liability_types: list[int]
        | None = None,
    ):
        cond = [
            Liability.user_id == user_id,
            Liability.deleted_id == "0",
        ]

        if liability_types:
            cond.append(
                Liability.liability_type.in_(
                    liability_types
                )
            )

        stmt = (
            select(Liability)
            .where(*cond)
            .order_by(
                Liability.ctime.desc()
            )
        )

        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def total_liability(
        self,
        session,
        user_id: int,
    ):
        cond = [
            Liability.user_id == user_id,
            Liability.deleted_id == "0",
            Liability.status
            == LiabilityStatus.ACTIVE,
        ]

        stmt = select(
            func.coalesce(
                func.sum(
                    Liability.remaining_principal
                ),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)

        return ret.scalar_one()

    async def liability_status_summary(
        self,
        session,
        user_id: int,
    ):
        cond = [
            Liability.user_id == user_id,
            Liability.deleted_id == "0",
        ]

        stmt = (
            select(
                Liability.status,
                func.count(
                    Liability.id
                ).label("count"),
            )
            .where(*cond)
            .group_by(
                Liability.status
            )
        )

        ret = await session.execute(stmt)

        return ret.all()

    # ==========================
    # Goal
    # ==========================

    async def query_goals(
        self,
        session,
        user_id: int,
        *,
        goal_ids: list[str] | None = None,
    ) -> List[Goal]:

        cond = [
            Goal.user_id == user_id,
            Goal.deleted_id == "0",
        ]

        if goal_ids:
            cond.append(
                Goal.id.in_(goal_ids)
            )

        stmt = (
            select(Goal)
            .where(*cond)
            .order_by(
                Goal.priority.asc(),
                Goal.deadline.asc(),
            )
        )

        ret = await session.execute(stmt)

        return ret.scalars().all()

    async def total_goal_target_amount(
        self,
        session,
        user_id: int,
    ):
        cond = [
            Goal.user_id == user_id,
            Goal.deleted_id == "0",
        ]

        stmt = select(
            func.coalesce(
                func.sum(
                    Goal.target_amount
                ),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)

        return ret.scalar_one()

    async def total_goal_current_amount(
        self,
        session,
        user_id: int,
    ):
        cond = [
            Goal.user_id == user_id,
            Goal.deleted_id == "0",
        ]

        stmt = select(
            func.coalesce(
                func.sum(
                    Goal.current_amount
                ),
                0,
            )
        ).where(*cond)

        ret = await session.execute(stmt)

        return ret.scalar_one()


fin_analysis_repo = FinancialAnalysisRepo()