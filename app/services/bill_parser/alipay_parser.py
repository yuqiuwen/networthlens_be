import csv
import io
from typing import BinaryIO

import pandas as pd

from app.constant import TransactionChannel, TransactionStatus, TransactionType
from app.services.bill_parser.base import BillRecord, yuan_to_cent


DIRECTION_MAP = {"支出": TransactionType.EXPENSE, "收入": TransactionType.INCOME}
AMOUNT_COLUMNS = ("金额（元）", "金额(元)")


class AlipayBillParser:
    """Parse Alipay transaction-detail exports into normalized bill records."""

    @staticmethod
    def find_header_row(file: BinaryIO, filename: str | None = None) -> int:
        """Return the row index containing the Alipay bill headers."""
        file.seek(0)
        preview = AlipayBillParser._read_bill(file, filename, header=None, dtype=str)
        required = {"交易号", "收/支"}

        for index, row in preview.iterrows():
            values = set(row.fillna("").astype(str).str.strip().tolist())
            if required.issubset(values) and any(column in values for column in AMOUNT_COLUMNS):
                return index

        raise ValueError("未找到支付宝账单表头")

    @staticmethod
    def parse(file: BinaryIO, filename: str | None = None) -> list[BillRecord]:
        """Parse an uploaded Alipay bill workbook or CSV export."""
        header_row = AlipayBillParser.find_header_row(file, filename)
        file.seek(0)
        df = AlipayBillParser._read_bill(file, filename, header=header_row)
        amount_column = next((column for column in AMOUNT_COLUMNS if column in df.columns), None)

        if amount_column is None:
            raise ValueError("支付宝账单缺少金额列")

        records: list[BillRecord] = []
        for _, row in df.iterrows():
            transaction_id = row.get("交易号")
            if pd.isna(transaction_id):
                continue

            transaction_type = DIRECTION_MAP.get(str(row.get("收/支", "")).strip())
            if transaction_type is None:
                continue

            transaction_status = str(row.get("交易状态", ""))
            remark = row.get("备注")
            note = None if pd.isna(remark) or remark == "/" else str(remark)
            occurred_at = row.get("付款时间")
            if pd.isna(occurred_at) or not str(occurred_at).strip():
                occurred_at = row.get("交易创建时间")
            if pd.isna(occurred_at) or not str(occurred_at).strip():
                continue

            records.append(
                BillRecord(
                    channel=TransactionChannel.ALIPAY,
                    transaction_id=str(transaction_id),
                    occurred_at=pd.to_datetime(occurred_at).to_pydatetime(),
                    transaction_type=transaction_type,
                    merchant=(None if pd.isna(row.get("交易对方")) else str(row.get("交易对方"))),
                    product=(None if pd.isna(row.get("商品名称")) else str(row.get("商品名称"))),
                    amount=yuan_to_cent(row[amount_column]),
                    source_account_id=None,
                    target_account_id=None,
                    status=(
                        TransactionStatus.REFUNDED
                        if "退款" in transaction_status
                        else TransactionStatus.NORMAL
                    ),
                    note=note,
                )
            )

        return records

    @staticmethod
    def _read_bill(file: BinaryIO, filename: str | None, **kwargs) -> pd.DataFrame:
        """Read an Alipay bill from an Excel workbook or a CSV export."""
        if (filename or "").lower().endswith(".csv"):
            content = file.read()
            rows = None
            for encoding in ("utf-8-sig", "gb18030"):
                try:
                    rows = list(csv.reader(io.StringIO(content.decode(encoding))))
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
            return pd.DataFrame(rows[header + 1 :], columns=rows[header])
        return pd.read_excel(file, **kwargs)
