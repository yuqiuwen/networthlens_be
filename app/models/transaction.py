from app.constant import TransactionStatus
from app.models.module import *


class Transaction(BaseModel, TimeModel):
    """
    交易流水表

    字段说明：
    - id: {year}{mon}{day}{time}{version}{user_id}{random}, {年月日8位}{时间6位}{版本号1位}{用户id后4位}{随机序列号2位}
    - transaction_type: TransactionType
    - status: TransactionStatus
    - merchant: 商户
    - account_id
    - source_account_id: 支出/转出账户
    - target_account_id: 收入/转入账户
    - amount: 金额，统一按最小货币单位存储，且始终存正数
    """

    __tablename__ = "transaction"

    id = Column(String(21), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    transaction_type = Column(SmallInteger, nullable=False)
    transaction_id = Column(String(100), nullable=False, unique=True)
    category_id = Column(String(26))
    source_account_id = Column(String(26), index=True)
    target_account_id = Column(String(26), index=True)
    product = Column(String)
    amount = Column(BigInteger, nullable=False, server_default=text("0"))
    currency = Column(CHAR(3), nullable=False, server_default=text("'CNY'"))
    occurred_at = Column(DateTime, nullable=False, server_default=func.now())
    merchant = Column(String(100))
    note = Column(Text)
    status = Column(SmallInteger, nullable=False, default=TransactionStatus.NORMAL)
    deleted_id = Column(String(26), nullable=False, server_default="0")

    __table_args__ = (
        Index(None, "user_id", "occurred_at"),
        Index(None, "user_id", "transaction_type"),
    )


class TransactionTag(BaseModel):
    """
    交易-标签关联表

    字段说明：
    - transaction_id / tag_id: 多对多关联字段
    """

    __tablename__ = "transaction_tag"

    transaction_id = Column(String(21), primary_key=True)
    tag_id = Column(String(26), primary_key=True)
