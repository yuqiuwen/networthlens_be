import pandas as pd


from app.constant import TransactionStatus, TransactionType
from app.services.bill_parser.base import BillRecord, yuan_to_cent


PAYMENT_METHOD_ACCOUNT_MAP = {
    "招商银行储蓄卡(4288)": "01KT90HZCS0EDDCZRJC4YPMZMV",
    "零钱": ""
}

DRIECTION_MAP = {"支出": TransactionType.EXPENSE, "收入": TransactionType.INCOME}


class WechatBillParser:
    def find_header_row(file_path: str) -> int:
        preview = pd.read_excel(
            file_path,
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
            values = set(row.fillna("").astype(str).tolist())

            if required.issubset(values):
                return idx

        raise ValueError("未找到微信账单表头")

    def parse(self, file_path: str) -> list[BillRecord]:
        header_row = self.find_header_row(file_path)

        df = pd.read_excel(
            file_path,
            header=header_row,
        )

        records = []

        for _, row in df.iterrows():
            transaction_id = row.get("交易单号")

            if pd.isna(transaction_id):
                continue

            records.append(
                BillRecord(
                    transaction_id=str(transaction_id),
                    occurred_at=pd.to_datetime(row["交易时间"]).to_pydatetime(),
                    transaction_type=DRIECTION_MAP.get(str(row["收/支"]).strip()),
                    merchant=(None if pd.isna(row["交易对方"]) else str(row["交易对方"])),
                    product=(None if pd.isna(row["商品"]) else str(row["商品"])),
                    amount=yuan_to_cent(row["金额(元)"]),
                    payment_method=(None if pd.isna(row["支付方式"]) else str(row["支付方式"])),
                    status=TransactionStatus.NORMAL,
                    note=(None if (pd.isna(row["备注"]) or row["备注"] == "/") else str(row["备注"])),
                )
            )

        return records
