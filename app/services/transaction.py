from datetime import datetime
from typing import Literal
from app.core.exception import APIException
from app.repo.transaction import transaction_repo
from app.schemas.transaction import CreateTransactionSchema, TransactionQuerySchema, UpdateTransactionSchema
from app.services.bill_parser.wechat_parser import WechatBillParser
from app.utils.common import gen_ulid


class TransactionService:
    async def create(
        self,
        session,
        cur_user,
        data: CreateTransactionSchema,
    ):

        ret = await transaction_repo.add(session, cur_user, data)
        
        return ret


    async def create_by_agent(
        self,
        session,
        user_id: int,
        transaction_type: int,
        amount: int,
        currency: str = "CNY",
        category_id: str | None = None,
        source_account_id: str | None = None,
        target_account_id: str | None = None,
        merchant: str | None = None,
        product: str | None = None,
        occurred_at=None,
        note: str | None = None,
        ):
        """
        Agent专用创建流水

        当前版本：

            只创建流水

        后续版本：

            自动更新账户余额
            自动更新负债
            自动更新目标
        """

        if occurred_at is None:
            occurred_at = datetime.now()

        transaction = (
            await transaction_repo.create(
                session,
                {
                    "id": gen_ulid(),
                    "user_id": user_id,
                    "transaction_type": transaction_type,
                    "category_id": category_id,
                    "source_account_id": source_account_id,
                    "target_account_id": target_account_id,
                    "amount": amount,
                    "currency": currency,
                    "merchant": merchant,
                    "product": product,
                    "occurred_at": occurred_at,
                    "note": note,
                },
            )
        )

        return transaction.id
        


    async def list(
        self,
        session,
        cur_user,
        query: TransactionQuerySchema,
    ):
        
        paged = await transaction_repo.page(
            session,
            cur_user.id,
            query,
        )
        

        return paged


    async def detail(
        self,
        session,
        cur_user,
        transaction_id,
    ):
        transaction = (
            await transaction_repo.detail(
                session,
                transaction_id,
                cur_user.id,
            )
        )

        if not transaction:
            raise APIException(
                "流水不存在",
                code=404,
            )

        return transaction


    async def update(
        self,
        session,
        cur_user,
        transaction_id,
        data: UpdateTransactionSchema,
    ):
        transaction = (
            await transaction_repo.detail(
                session,
                transaction_id,
                cur_user.id,
            )
        )

        if not transaction:
            raise APIException(
                "流水不存在",
                code=404,
            )

        await transaction_repo.update(
            session,
            transaction,
            data.model_dump(
                exclude_unset=True
            ),
        )

        return True


    async def delete(
        self,
        session,
        cur_user,
        transaction_id,
    ):
        transaction = (
            await transaction_repo.detail(
                session,
                transaction_id,
                cur_user.id,
            )
        )

        if not transaction:
            raise APIException(
                "流水不存在",
                code=404,
            )

        await transaction_repo.soft_delete(
            session,
            transaction_id,
            cur_user.id,
        )

        return True


    async def import_excel(
        self,
        session,
        cur_user,
        import_source: Literal["wx", "alipay"],
        file,
    ):
        rows = []
        if import_source == "wx":
            rows = WechatBillParser().parse(file)

        if not rows:
            return {
                "success_count": 0,
                "failed_count": 0,
            }

        data = []

        for row in rows:
            item = row.model_dump()
            item.pop("payment_method")
            data.append(
                {
                    "id": gen_ulid(),
                    "user_id": cur_user.id,
                    **item,
                }
            )

        

        await transaction_repo.batch_create(
            session,
            data,
        )

        return {
            "success_count": len(data),
            "failed_count": 0,
        }

    async def export_excel(
        self,
        session,
        cur_user,
        query,
    ):
        ...