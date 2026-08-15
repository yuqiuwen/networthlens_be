from app.constant import (
    AccountStatus,
    AssetStatus,
    AssetValuationMethod,
    DataJobStatus,
    GoalStatus,
    LiabilityStatus,
    ReminderStatus,
    TagStatus,
    TransactionStatus,
)
from app.models.module import *


class Account(BaseModel, TimeModel):
    """
    账户表

    字段说明：
    - account_type: AccountType
    - status: AccountStatus
    - balance: 当前余额，按最小货币单位存储
    - available_balance: 可用余额，按最小货币单位存储
    - credit_limit: 信用额度，按最小货币单位存储
    """

    __tablename__ = "account"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    account_type = Column(SmallInteger, nullable=False)
    name = Column(String(100), nullable=False)
    currency = Column(CHAR(3), nullable=False, server_default=text("'CNY'"))
    balance = Column(BigInteger, nullable=False, server_default=text("0"))
    available_balance = Column(BigInteger, nullable=False, server_default=text("0"))
    credit_limit = Column(BigInteger)
    icon = Column(Text)
    status = Column(SmallInteger, nullable=False, index=True, default=AccountStatus.NORMAL)
    sort_no = Column(Integer, nullable=False, server_default=text("0"))
    note = Column(String(500))
    deleted_id = Column(String(26), nullable=False, server_default="0")

    __table_args__ = (Index(None, "user_id"),)


class Category(BaseModel, TimeModel):
    """
    分类表

    字段说明：
    - category_type: CategoryType
    - parent_id: 父分类ID
    """

    __tablename__ = "category"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger)
    code = Column(String(50))
    category_type = Column(SmallInteger, nullable=False)
    parent_id = Column(String(26), nullable=True, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(50))
    color = Column(String(20))
    sort_no = Column(Integer, nullable=False, server_default=text("0"))
    status = Column(SmallInteger, nullable=False, server_default=text("1"))
    deleted_id = Column(String(26), nullable=False, default="0")

    __table_args__ = (
        Index(None, "user_id", "category_type"),
        UniqueConstraint("user_id", "code", name=None)
    )



class Asset(BaseModel, TimeModel):
    """
    资产表（房产、车辆、收藏品、其他）

    字段说明：
    - asset_type: AssetType
    - valuation_method: AssetValuationMethod 估值方式
    - status: AssetStatus
    - quantity: 数量/面积/份额等
    - unit_price: 单价
    - purchase_amount: 购入总金额，按最小货币单位存储
    - current_value: 当前估值，按最小货币单位存储
    - extra_info: 额外信息
    """

    __tablename__ = "asset"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    asset_type = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    quantity = Column(Numeric(24, 8), nullable=False, server_default=text("0"))
    unit = Column(String(20))
    purchase_amount = Column(BigInteger, nullable=False, server_default=text("0"))
    current_value = Column(BigInteger, nullable=False, server_default=text("0"))
    unit_price = Column(Numeric(24, 8))
    currency = Column(CHAR(3), nullable=False, server_default=text("'CNY'"))
    purchase_date = Column(Date)
    valuation_method = Column(SmallInteger, nullable=False, default=AssetValuationMethod.MANUAL)
    status = Column(SmallInteger, nullable=False, default=AssetStatus.NORMAL)
    image_urls = Column(ARRAY(String(100)))
    extra_info = Column(JSON)
    note = Column(Text)
    deleted_id = Column(String(26), nullable=False, default="0")

    __table_args__ = (
        Index(None, "user_id", "asset_type"),
        Index(None, "user_id", "status"),
    )


class AssetValuationHistory(BaseModel, TimeModel):
    """
    资产估值历史表

    字段说明：
    - valuation: 估值金额，按最小货币单位存储
    - source: AssetValuationSource
    """

    __tablename__ = "asset_valuation_history"

    id = Column(String(26), primary_key=True)
    asset_id = Column(String(26), nullable=False)
    valuation = Column(BigInteger, nullable=False, server_default=text("0"))
    valuation_date = Column(Date, nullable=False)
    source = Column(SmallInteger, nullable=False)
    note = Column(
        String(500),
    )

    __table_args__ = (Index(None, "asset_id", "valuation_date"),)


class Liability(BaseModel, TimeModel):
    """
    负债表

    字段说明：
    - liability_type: LiabilityType
    - repayment_type: RepaymentType
    - status: LiabilityStatus
    - original_principal: 初始本金，按最小货币单位存储
    - remaining_principal: 剩余本金，按最小货币单位存储
    - monthly_payment: 每月还款额，按最小货币单位存储
    - interest_rate: 年化利率
    """

    __tablename__ = "liability"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    liability_type = Column(SmallInteger, nullable=False)
    name = Column(String(100), nullable=False)
    original_principal = Column(BigInteger, nullable=False, server_default=text("0"))
    remaining_principal = Column(BigInteger, nullable=False, server_default=text("0"))
    interest_rate = Column(Numeric(10, 6), nullable=False, server_default=text("0"))
    repayment_type = Column(SmallInteger, nullable=False)
    monthly_payment = Column(BigInteger)
    currency = Column(CHAR(3), nullable=False, server_default=text("'CNY'"))
    start_date = Column(
        Date,
    )
    due_date = Column(
        Date,
    )
    status = Column(SmallInteger, nullable=False, default=LiabilityStatus.ACTIVE)
    note = Column(
        Text,
    )
    deleted_id = Column(String(26), nullable=False, default="0")

    __table_args__ = (
        Index(None, "user_id", "status"),
        Index(None, "due_date"),
    )


class LiabilityRepayment(BaseModel, TimeModel):
    """
    负债还款记录表

    字段说明：
    - liability_id / transaction_id: 关联字段
    - repayment_amount: 还款总额，按最小货币单位存储
    - principal: 还本金，按最小货币单位存储
    - interest: 还利息，按最小货币单位存储
    - fee: 手续费，按最小货币单位存储
    """

    __tablename__ = "liability_repayment"

    id = Column(String(26), primary_key=True)
    liability_id = Column(String(26), nullable=False)
    transaction_id = Column(String(21))
    repayment_amount = Column(BigInteger, nullable=False, server_default=text("0"))
    principal = Column(BigInteger, nullable=False, server_default=text("0"))
    interest = Column(BigInteger, nullable=False, server_default=text("0"))
    fee = Column(BigInteger, nullable=False, server_default=text("0"))
    remaining_principal = Column(BigInteger, nullable=False, server_default=text("0"))
    paid_at = Column(DateTime, nullable=False, server_default=func.now())
    note = Column(
        String(500),
    )

    __table_args__ = (Index(None, "liability_id", "paid_at"),)


class InvestmentHolding(BaseModel, TimeModel):
    """
    投资持仓表

    字段说明：
    - holding_type: HoldingType
    - status: HoldingStatus
    - quantity / available_quantity: 持有数量 / 可卖数量
    - avg_cost_price / latest_price: 成本价 / 最新价
    - cost_value / market_value / profit_loss: 金额类字段，按最小货币单位存储
    - profit_loss_rate: 盈亏率
    """

    __tablename__ = "investment_holding"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    account_id = Column(String(26))
    holding_type = Column(SmallInteger, nullable=False)
    symbol = Column(String(30), nullable=False)
    name = Column(String(100), nullable=False)
    exchange_code = Column(
        String(20),
    )
    quantity = Column(Numeric(24, 8), nullable=False, server_default=text("0"))
    available_quantity = Column(Numeric(24, 8), nullable=False, server_default=text("0"))
    avg_cost_price = Column(Numeric(24, 8), nullable=False, server_default=text("0"))
    latest_price = Column(Numeric(24, 8), nullable=False, server_default=text("0"))
    cost_value = Column(BigInteger, nullable=False, server_default=text("0"))
    market_value = Column(BigInteger, nullable=False, server_default=text("0"))
    profit_loss = Column(BigInteger, nullable=False, server_default=text("0"))
    profit_loss_rate = Column(Numeric(18, 8), nullable=False, server_default=text("0"))
    currency = Column(CHAR(3), nullable=False, server_default=text("'CNY'"))
    last_quote_at = Column(
        DateTime,
    )
    status = Column(SmallInteger, nullable=False, server_default=text("1"))
    note = Column(
        Text,
    )
    deleted_id = Column(String(26), nullable=False, default="0")

    __table_args__ = (
        Index("idx_holding_user_type", "user_id", "holding_type"),
        Index("idx_holding_symbol", "symbol", "exchange_code"),
    )


class Goal(BaseModel, TimeModel):
    """
    财务目标表

    字段说明：
    - goal_type: GoalType
    - status: GoalStatus
    - target_amount: 目标金额，按最小货币单位存储
    - current_amount: 当前进度金额，按最小货币单位存储
    - priority: 优先级，数值越小优先级越高
    """

    __tablename__ = "goal"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    goal_type = Column(SmallInteger, nullable=False)
    name = Column(String(100), nullable=False)
    target_amount = Column(BigInteger, nullable=False, server_default=text("0"))
    current_amount = Column(BigInteger, nullable=False, server_default=text("0"))
    start_date = Column(
        Date,
    )
    deadline = Column(Date, index=True)
    priority = Column(SmallInteger, nullable=False, server_default=text("100"))
    status = Column(SmallInteger, nullable=False, default=GoalStatus.IN_PROGRESS)
    note = Column(
        Text,
    )
    deleted_id = Column(String(26), nullable=False, default="0")

    __table_args__ = (Index(None, "user_id", "status"),)


class GoalContribution(BaseModel, TimeModel):
    """
    目标资金记录表

    字段说明：
    - goal_id / account_id / transaction_id: 逻辑关联字段
    - amount: 追加金额，按最小货币单位存储
    - contributed_at: 追加时间
    """

    __tablename__ = "goal_contribution"

    id = Column(String(26), primary_key=True)
    goal_id = Column(String(26), nullable=False)
    account_id = Column(
        String(26),
    )
    transaction_id = Column(
        String(21),
    )
    amount = Column(BigInteger, nullable=False, server_default=text("0"))
    contributed_at = Column(DateTime, nullable=False, server_default=func.now())
    note = Column(
        String(500),
    )

    __table_args__ = (Index(None, "goal_id", "contributed_at"),)


class Reminder(BaseModel, TimeModel):
    """
    提醒表

    字段说明：
    - reminder_type: ReminderType
    - related_object_type: RelatedObjectType
    - schedule_type: ScheduleType
    - status: ReminderStatus
    - cron_expr: 周期表达式
    - next_run_at / remind_at / snooze_until: 提醒调度时间
    """

    __tablename__ = "reminder"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    reminder_type = Column(SmallInteger, nullable=False)
    title = Column(String(100), nullable=False)
    related_object_type = Column(SmallInteger)
    related_object_id = Column(String(26))
    schedule_type = Column(SmallInteger, nullable=False)
    cron_expr = Column(String(100))
    next_run_at = Column(DateTime)
    remind_at = Column(
        DateTime,
    )
    status = Column(SmallInteger, nullable=False, default=ReminderStatus.ENABLED)
    snooze_until = Column(DateTime)
    note = Column(
        String(500),
    )
    deleted_id = Column(String(26), nullable=False, default="0")

    __table_args__ = (
        Index("idx_reminder_user_next", "user_id", "next_run_at"),
        Index("idx_reminder_status", "status"),
    )


class Tag(BaseModel, TimeModel):
    """
    标签表

    字段说明：
    - status: TagStatus
    """

    __tablename__ = "tag"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(
        String(20),
    )
    status = Column(SmallInteger, nullable=False, default=TagStatus.ENABLED)
    deleted_id = Column(String(26), nullable=False, default="0")





class Attachment(BaseModel, TimeModel):
    """
    附件表

    字段说明：
    - related_object_type: RelatedObjectType
    - related_object_id: 关联对象ID
    - file_name / file_url / file_size / mime_type: 附件基础信息
    """

    __tablename__ = "attachment"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    related_object_type = Column(SmallInteger, nullable=False)
    related_object_id = Column(String(26), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False, server_default=text("0"))
    mime_type = Column(
        String(100),
    )

    __table_args__ = (
        Index(None, "related_object_type", "related_object_id"),
        Index(None, "user_id"),
    )


class ExchangeRate(BaseModel, TimeModel):
    """
    汇率表

    字段说明：
    - source: ExchangeRateSource
    - rate: 汇率
    - rate_date: 汇率日期
    """

    __tablename__ = "exchange_rate"

    id = Column(BigInteger, primary_key=True)
    base_currency = Column(CHAR(3), nullable=False)
    quote_currency = Column(CHAR(3), nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    rate_date = Column(Date, nullable=False)
    source = Column(SmallInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "base_currency",
            "quote_currency",
            "rate_date",
            name="uk_exchange_rate_pair_date",
        ),
    )


class AuditLog(BaseModel, TimeModel):
    """
    审计日志表

    字段说明：
    - action_type: AuditActionType
    - object_type: AuditObjectType
    - object_id: 被操作对象ID
    - before_data / after_data: 操作前后快照
    - ip: 操作 IP
    """

    __tablename__ = "audit_log"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    action_type = Column(SmallInteger, nullable=False)
    object_type = Column(SmallInteger, nullable=False)
    object_id = Column(String(26), nullable=False)
    before_data = Column(
        JSON,
    )
    after_data = Column(
        JSON,
    )
    ip = Column(
        String(45),
    )

    __table_args__ = (Index(None, "user_id", "ctime"),)


class DataJob(BaseModel, TimeModel):
    """
    导入导出任务表

    字段说明：
    - job_type: JobType
    - module_type: ModuleType
    - status: DataJobStatus
    - file_url: 任务文件地址
    - error_message: 错误信息
    """

    __tablename__ = "data_job"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    job_type = Column(SmallInteger, nullable=False)
    module_type = Column(SmallInteger, nullable=False)
    file_url = Column(
        String(500),
    )
    status = Column(SmallInteger, nullable=False, default=DataJobStatus.PROCESSING)
    error_message = Column(
        String(1000),
    )

    __table_args__ = (Index(None, "user_id", "status"),)


class RecurringRule(BaseModel, TimeModel):
    """
    周期规则表

    字段说明：
    - rule_type: RuleType
    - interval_unit: IntervalUnit
    - template_transaction_id: 模板流水ID
    - interval_count: 周期数
    - next_run_at / end_date: 调度时间
    - template_json: 规则扩展信息
    """

    __tablename__ = "recurring_rule"

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    rule_type = Column(SmallInteger, nullable=False)
    template_transaction_id = Column(
        String(21),
    )
    interval_unit = Column(SmallInteger, nullable=False)
    interval_count = Column(Integer, nullable=False, server_default=text("1"))
    next_run_at = Column(
        DateTime,
    )
    end_date = Column(
        Date,
    )
    status = Column(SmallInteger, nullable=False, server_default=text("1"))
    template_json = Column(
        JSON,
    )

    __table_args__ = (Index(None, "user_id", "next_run_at"),)
