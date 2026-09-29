import random
from app.constant import TransactionChannel, TransactionStatus
from app.models.module import *
from app.utils.dater import DT


def gen_transaction_id(user_id: int, version=1):
    now = DT.now_time()
    return f"{now.strftime("%Y%m%d%H%M%S%f")[:-3]}{version}{str(user_id)[-4:].zfill(4)}{random.randint(0, 9999):04d}"


class Transaction(BaseModel, TimeModel):
    """
    交易流水表

    字段说明：
    - id: {year}{mon}{day}{time}{version}{user_id}{random}, {年月日8位}{时间9位}{版本号1位}{用户id后4位}{随机序列号4位}
    - transaction_type: TransactionType
    - status: TransactionStatus
    - channel: TransactionChannel
    - merchant: 商户
    - account_id
    - source_account_id: 支出/转出账户
    - target_account_id: 收入/转入账户
    - amount: 金额，统一按最小货币单位存储，且始终存正数
    """

    __tablename__ = "transaction"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    channel = Column(SmallInteger, nullable=False, default=TransactionChannel.OTHER)
    transaction_type = Column(SmallInteger, nullable=False)
    transaction_id = Column(String(100), nullable=False)
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
        UniqueConstraint("channel", "transaction_id", name=None)
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


class TransactionCategoryWord(BaseModel, TSModel, StateModel):
    """交易单分类匹配词"""

    __tablename__ = "transaction_category_reg_word"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name=None),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    words = Column(ARRAY(String(30)), nullable=False)
    category_id = Column(String(26), nullable=False)
    priority = Column(Integer, nullable=False, default=0, server_default=text('0'))
    description = Column(String(100), comment="描述")

    category = relationship(
        "Category",
        primaryjoin="foreign(TransactionCategoryWord.category_id) == Category.id",
        viewonly=True,
        lazy="selectin",
    )