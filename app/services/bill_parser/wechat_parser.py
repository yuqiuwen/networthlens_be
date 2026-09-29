import csv
import io
from collections.abc import Iterable, Mapping
from typing import BinaryIO, Sequence

from app.schemas.transaction import TransCategoryWordItem
import pandas as pd

from app.constant import CategoryType, TransactionChannel, TransactionStatus, TransactionType
from app.services.bill_parser.base import BillRecord, yuan_to_cent


DIRECTION_MAP = {
    "支出": TransactionType.EXPENSE,
    "收入": TransactionType.INCOME,
}

TRANSACTION_CATEGORY_TYPE_MAP = {
    TransactionType.INCOME: CategoryType.INCOME,
    TransactionType.EXPENSE: CategoryType.EXPENSE,
}


class WechatBillParser:
    @staticmethod
    def find_header_row(
        file: BinaryIO,
        filename: str | None = None,
    ) -> int:
        """Return the row index containing the WeChat bill headers."""
        file.seek(0)
        preview = WechatBillParser._read_bill(
            file,
            filename,
            header=None,
            dtype=str,
        )

        required = {
            "交易时间",
            "交易类型",
            "金额(元)",
            "交易单号",
        }

        for idx, row in preview.iterrows():
            values = {str(value).strip() for value in row if not pd.isna(value)}

            if required.issubset(values):
                return idx

        raise ValueError("未找到微信账单表头")

    @staticmethod
    def parse(
        file: BinaryIO,
        filename: str | None = None,
        account_mapping: Mapping[str, str] | None = None,
        category_rules: Sequence[TransCategoryWordItem]  | None = None,
    ) -> list[BillRecord]:
        """
        Parse a WeChat bill.

        TransactionCategoryWord.words 中存放普通关键词，不作为正则表达式处理。
        """
        return WechatBillParser._parse(
            file=file,
            filename=filename,
            account_mapping=account_mapping,
            category_rules=category_rules or [],
        )

    @staticmethod
    def extract_payment_methods(
        file: BinaryIO,
        filename: str | None = None,
    ) -> set[str]:
        """Return all non-empty payment methods present in a WeChat bill."""
        header_row = WechatBillParser.find_header_row(file, filename)

        file.seek(0)
        df = WechatBillParser._read_bill(
            file,
            filename,
            header=header_row,
        )

        if "支付方式" not in df.columns:
            raise ValueError("微信账单缺少支付方式列")

        return {
            value
            for payment_method in df["支付方式"]
            if (value := WechatBillParser._string_value(payment_method))
        }

    @staticmethod
    def _parse(
        file: BinaryIO,
        filename: str | None,
        account_mapping: Mapping[str, str] | None,
        category_rules: Sequence[TransCategoryWordItem],
    ) -> list[BillRecord]:
        header_row = WechatBillParser.find_header_row(
            file,
            filename,
        )

        file.seek(0)
        df = WechatBillParser._read_bill(
            file,
            filename,
            header=header_row,
        )

        WechatBillParser._validate_columns(df)

        records: list[BillRecord] = []

        for _, row in df.iterrows():
            transaction_id = WechatBillParser._row_string(
                row,
                "交易单号",
            )
            if not transaction_id:
                continue

            direction = WechatBillParser._row_string(
                row,
                "收/支",
            )

            transaction_type = DIRECTION_MAP.get(direction)
            if transaction_type is None:
                # 微信账单里可能存在“不计收支”等记录
                continue

            occurred_at = pd.to_datetime(
                row.get("交易时间"),
                errors="coerce",
            )
            if pd.isna(occurred_at):
                continue

            current_status = (
                WechatBillParser._row_string(
                    row,
                    "当前状态",
                )
                or ""
            )

            remark = WechatBillParser._row_string(
                row,
                "备注",
            )

            if remark and remark != "/":
                note = f"[{current_status}] {remark}"
            else:
                note = f"[{current_status}]"

            status = (
                TransactionStatus.REFUNDED if "退款" in current_status else TransactionStatus.NORMAL
            )

            payment_method = WechatBillParser._row_string(
                row,
                "支付方式",
            )

            account_id = (
                account_mapping.get(payment_method) if account_mapping and payment_method else None
            )

            if transaction_type == TransactionType.INCOME:
                source_account_id = None
                target_account_id = account_id
            else:
                source_account_id = account_id
                target_account_id = None

            merchant = WechatBillParser._row_string(
                row,
                "交易对方",
            )

            product = WechatBillParser._row_string(
                row,
                "商品",
            )

            wechat_transaction_type = WechatBillParser._row_string(
                row,
                "交易类型",
            )

            category_id = WechatBillParser._match_category(
                rules=category_rules,
                bill_transaction_type=transaction_type,
                merchant=merchant,
                transaction_name=wechat_transaction_type,
                product=product,
            )

            amount_value = row.get("金额(元)")
            if pd.isna(amount_value):
                continue

            amount = yuan_to_cent(amount_value)

            if transaction_type == TransactionType.EXPENSE:
                amount = -amount

            records.append(
                BillRecord(
                    channel=TransactionChannel.WX,
                    transaction_id=transaction_id,
                    occurred_at=occurred_at.to_pydatetime(),
                    transaction_type=transaction_type,
                    merchant=merchant,
                    product=product,
                    amount=amount,
                    source_account_id=source_account_id,
                    target_account_id=target_account_id,
                    status=status,
                    category_id=category_id,
                    note=note,
                )
            )

        return records

    @staticmethod
    def _match_category(
        rules: Sequence[TransCategoryWordItem],
        bill_transaction_type: TransactionType,
        merchant: str | None,
        transaction_name: str | None,
        product: str | None,
    ) -> str | None:
        """
        根据分类关键词自动匹配分类。

        规则：
        1. 收入只匹配收入分类，支出只匹配支出分类
        2. priority 越大优先级越高
        3. 同一规则 words 中任意关键词匹配即可
        4. 匹配范围：交易对方、交易类型、商品
        5. words 按普通字符串处理，不作为正则
        """
        expected_category_type = TRANSACTION_CATEGORY_TYPE_MAP.get(
            bill_transaction_type
        )

        if expected_category_type is None:
            return None

        targets = (
            merchant or "",
            transaction_name or "",
            product or "",
        )

        for rule in rules:
            category = rule.category

            if not category:
                continue

            if category.category_type != expected_category_type:
                continue

            for word in rule.words:
                keyword = str(word).strip()

                if not keyword:
                    continue

                if any(
                    keyword in target
                    for target in targets
                ):
                    return category.id

        return None


    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        """Validate required WeChat bill columns."""
        required = {
            "交易时间",
            "交易类型",
            "交易对方",
            "商品",
            "收/支",
            "金额(元)",
            "支付方式",
            "当前状态",
            "交易单号",
        }

        missing = required.difference(df.columns)

        if missing:
            raise ValueError(f"微信账单缺少必要列：{', '.join(sorted(missing))}")

    @staticmethod
    def _row_string(
        row: pd.Series,
        column: str,
    ) -> str | None:
        return WechatBillParser._string_value(row.get(column))

    @staticmethod
    def _string_value(value) -> str | None:
        if value is None or pd.isna(value):
            return None

        value = str(value).strip()

        if not value:
            return None

        return value

    @staticmethod
    def _read_bill(
        file: BinaryIO,
        filename: str | None,
        **kwargs,
    ) -> pd.DataFrame:
        """Read a WeChat bill from an Excel workbook or CSV export."""
        if (filename or "").lower().endswith(".csv"):
            content = file.read()
            rows = None

            for encoding in (
                "utf-8-sig",
                "gb18030",
            ):
                try:
                    decoded = content.decode(encoding)
                    rows = list(csv.reader(io.StringIO(decoded)))
                    break
                except UnicodeDecodeError:
                    continue

            if rows is None:
                raise ValueError("无法读取 CSV 文件编码")

            header = kwargs.get("header")

            if header is None:
                return pd.DataFrame(rows)

            if header >= len(rows):
                raise ValueError("账单表头行超出文件范围")

            columns = [str(column).strip() for column in rows[header]]

            return pd.DataFrame(
                rows[header + 1 :],
                columns=columns,
            )

        return pd.read_excel(
            file,
            **kwargs,
        )
