from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.constant import TransactionType
import pandas as pd 



@dataclass
class BillRecord:
    transaction_id: str
    occurred_at: datetime

    transaction_type: str

    merchant: Optional[str]
    product: Optional[str]

    amount: int  # 分

    source_account_id: Optional[str]
    target_account_id: Optional[str]
    status: str
    note: Optional[str]


def yuan_to_cent(value) -> int:
    return int(Decimal(str(value)) * 100)




