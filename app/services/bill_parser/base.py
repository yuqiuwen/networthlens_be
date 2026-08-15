from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.constant import TransactionChannel, TransactionType
import pandas as pd 



@dataclass
class BillRecord:
    channel: TransactionChannel | None
    transaction_id: str
    occurred_at: datetime

    transaction_type: TransactionType

    merchant: Optional[str]
    product: Optional[str]

    amount: int  # 分
    category_id: str | None
    source_account_id: Optional[str]
    target_account_id: Optional[str]
    status: str
    note: Optional[str]


def yuan_to_cent(value) -> int:
    return int(Decimal(str(value)) * 100)



