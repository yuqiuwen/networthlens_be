from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.repo.category import category_repo
from app.schemas.category import CategorySchema
from fastapi import UploadFile

from app.constant import TransactionChannel, TransactionType
from app.core.exception import APIException
from app.repo.account import account_repo
from app.repo.transaction import transaction_repo
from app.schemas.transaction import CreateTransactionSchema, TransactionListSchema, TransactionQuerySchema, UpdateTransactionSchema
from app.services.bill_parser.alipay_parser import AlipayBillParser
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
        channel: TransactionChannel,
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
                    "channel": channel,
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
        category_ids = [i.category_id for i in  paged.items if i.category_id]
        if category_ids:
            items: list[TransactionListSchema] = []
            
            category_list = await category_repo.list_by_user(session, cur_user.id, ids=category_ids)
            category_mapping = {c.id: c for c in category_list}
            for t in paged.items:
                item = TransactionListSchema.model_validate(t)
                category = category_mapping.get(item.category_id)
                if category:
                    item.category = CategorySchema.model_validate(category, strict=False)
                items.append(item)

            paged.items = items
            return paged

        return paged


    async def summary(
        self,
        session,
        cur_user,
        *,
        transaction_type=None,
        start_time=None,
        end_time=None,
    ):
        income = 0
        expense = 0

        if transaction_type in (None, TransactionType.INCOME):
            income = await transaction_repo.sum_amount(
                session,
                cur_user.id,
                transaction_type=TransactionType.INCOME,
                start_time=start_time,
                end_time=end_time,
            )

        if transaction_type in (None, TransactionType.EXPENSE):
            expense = await transaction_repo.sum_amount(
                session,
                cur_user.id,
                transaction_type=TransactionType.EXPENSE,
                start_time=start_time,
                end_time=end_time,
            )

        income = int(income or 0)
        expense = int(expense or 0)
        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
        }


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
        file: UploadFile,
        account_id: str | None = None,
    ):
        """Import a payment-provider statement and ignore transactions seen before."""
        filename = file.filename or ""
        if Path(filename).suffix.lower() not in {".xlsx", ".xls", ".csv"}:
            raise APIException(errmsg="仅支持 Excel 或 CSV 格式的账单文件", code=400)

        if account_id:
            await account_repo.retrieve(session, account_id, cur_user.id)

        user_category = await category_repo.list_by_user(session, cur_user.id)
        category_mapping = {c.code: c.id for c in user_category}

        parser = WechatBillParser if import_source == "wx" else AlipayBillParser
        account_mapping = None
        try:
            await file.seek(0)
            if import_source == "wx":
                payment_methods = WechatBillParser.extract_payment_methods(file.file, filename)
                accounts = await account_repo.list_by_names(
                    session,
                    cur_user.id,
                    payment_methods,
                )
                account_mapping = {account.name: account.id for account in accounts}

            await file.seek(0)
            if import_source == "wx":
                rows = WechatBillParser.parse(
                    file.file,
                    filename,
                    account_mapping=account_mapping,
                    category_mapping=category_mapping
                )
            else:
                rows = parser.parse(file.file, filename)
        except (KeyError, TypeError, UnicodeDecodeError, ValueError) as exc:
            raise APIException(f"账单解析失败：{exc}", code=400, errmsg="账单解析失败") from exc

        if not rows:
            return {
                "success_count": 0,
                "failed_count": 0,
                "import_source": import_source,
            }

        data: list[dict] = []

        for row in rows:
            if account_id:
                if row.transaction_type == TransactionType.INCOME:
                    row.target_account_id = account_id
                elif row.transaction_type == TransactionType.EXPENSE:
                    row.source_account_id = account_id

            item = asdict(row)
            data.append(item)

        success_count = await transaction_repo.import_records(
            session,
            cur_user.id,
            data,
        )

        return {
            "success_count": success_count,
            "failed_count": 0,
            "import_source": import_source,
        }

    async def export_excel(
        self,
        session,
        cur_user,
        query,
    ):
        ...
