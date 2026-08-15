import csv
import io
import re
from typing import BinaryIO, Mapping

import pandas as pd

from app.constant import TransactionChannel, TransactionStatus, TransactionType
from app.services.bill_parser.base import BillRecord, yuan_to_cent


DIRECTION_MAP = {"支出": TransactionType.EXPENSE, "收入": TransactionType.INCOME}
CATEGORY_REG_MATCH_MAP = {
    "expense_shopping": r'(京东|淘宝|天猫|拼多多|唯品会)',
    "expense_traffic": r'(中铁网络|高德打车|携程|同程旅行|滴滴)',
}


class WechatBillParser:
    @staticmethod
    def find_header_row(file: BinaryIO, filename: str | None = None) -> int:
        """Return the row index containing the WeChat bill headers."""
        file.seek(0)
        preview = WechatBillParser._read_bill(file, filename, header=None, dtype=str)

        required = {
            "交易时间",
            "交易类型",
            "金额(元)",
            "交易单号",
        }

        for idx, row in preview.iterrows():
            values = set(row.fillna("").astype(str).tolist())

            if required.issubset(values):
                return idx

        raise ValueError("未找到微信账单表头")

    @staticmethod
    def parse(
        file: BinaryIO,
        filename: str | None = None,
        account_mapping: Mapping[str, str] | None = None,
        category_mapping: Mapping[str, str] | None = None,
    ) -> list[BillRecord]:
        """Parse a WeChat bill and resolve payment methods to account IDs."""
        return WechatBillParser._parse(file, filename, account_mapping, category_mapping)

    @staticmethod
    def extract_payment_methods(file: BinaryIO, filename: str | None = None) -> set[str]:
        """Return all non-empty payment methods present in a WeChat bill."""
        header_row = WechatBillParser.find_header_row(file, filename)
        file.seek(0)
        df = WechatBillParser._read_bill(file, filename, header=header_row)

        if "支付方式" not in df.columns:
            raise ValueError("微信账单缺少支付方式列")

        return {
            str(payment_method).strip()
            for payment_method in df["支付方式"]
            if not pd.isna(payment_method) and str(payment_method).strip()
        }

    @staticmethod
    def _parse(
        file: BinaryIO,
        filename: str | None,
        account_mapping: Mapping[str, str] | None = None,
        category_mapping: Mapping[str, str] | None = None,
    ) -> list[BillRecord]:
        header_row = WechatBillParser.find_header_row(file, filename)

        file.seek(0)
        df = WechatBillParser._read_bill(file, filename, header=header_row)

        records: list[BillRecord] = []

        for _, row in df.iterrows():
            transaction_id = row.get("交易单号")
            if pd.isna(transaction_id):
                continue

            transaction_type = DIRECTION_MAP.get(str(row.get("收/支", "")).strip())
            if transaction_type is None:
                continue

            current_status = str(row.get("当前状态", ""))
            remark = row.get("备注")
            if not (pd.isna(remark) or remark == "/"):
                note = f"[{current_status}] {str(remark)}"
            else:
                note = f"[{current_status}]"

            status = TransactionStatus.REFUNDED if "退款" in current_status else TransactionStatus.NORMAL
            payment_method = None if pd.isna(row["支付方式"]) else str(row["支付方式"]).strip()
            account_id = account_mapping.get(payment_method) if payment_method and account_mapping else None

            if transaction_type == TransactionType.INCOME:
                source_account_id = None
                target_account_id = account_id
            elif transaction_type == TransactionType.EXPENSE:
                source_account_id = account_id
                target_account_id = None
                for cc, reg in CATEGORY_REG_MATCH_MAP.items():
                    if re.compile(reg).search(row["交易对方"]):
                        category_code = cc 
                        break
                    category_code = None
                        
            else:
                source_account_id = target_account_id = None

            records.append(
                BillRecord(
                    channel=TransactionChannel.WX,
                    transaction_id=str(transaction_id),
                    occurred_at=pd.to_datetime(row["交易时间"]).to_pydatetime(),
                    transaction_type=transaction_type,
                    merchant=(None if pd.isna(row["交易对方"]) else str(row["交易对方"])),
                    product=(None if pd.isna(row["商品"]) else str(row["商品"])),
                    amount=yuan_to_cent(row["金额(元)"]),
                    source_account_id=source_account_id,
                    target_account_id=target_account_id,
                    status=status,
                    category_id=category_mapping.get(category_code),
                    note=note,
                )
            )

        return records

    @staticmethod
    def _read_bill(file: BinaryIO, filename: str | None, **kwargs) -> pd.DataFrame:
        """Read a WeChat bill from an Excel workbook or a CSV export."""
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
