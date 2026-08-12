from enum import IntEnum, Enum
from types import MappingProxyType


class EnumPro(Enum):
    def __new__(cls, value, desc):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.desc = desc
        return obj

    @classmethod
    def mappings(cls):
        return {c._value_: c.desc for c in cls}

    @classmethod
    def options(cls):
        return [{"name": c.desc, "value": c.value} for c in cls]


class IntEnumPro(IntEnum):
    def __new__(cls, value, desc):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.desc = desc
        return obj

    @classmethod
    def mappings(cls):
        return {c._value_: c.desc for c in cls}

    @classmethod
    def options(cls):
        return [{"name": c.desc, "value": c.value} for c in cls]


class UserType(IntEnumPro):
    NORMAL = 1, "普通用户"


class AuthType(IntEnumPro):
    PHONE = 1, "手机号"
    ACCOUNT = 2, "账号"
    EMAIL = 3, "邮箱"
    WX = 4, "微信"


class SMSSendBiz(EnumPro):
    """短信发送业务场景"""

    LOGIN = "login", "登录"
    SIGN = "sign", "注册"
    SET_PWD = "set_pwd", "设置密码"
    BIND_PHONE = "bind_phone", "绑定手机号"
    REVOKE = "revoke", "注销"


class UserRole(EnumPro):
    SUPER = "super", "超级管理员"
    ADMIN = "admin", "管理员"
    USER = "user", "用户"


class RepeatType(IntEnumPro):
    "重复类型"

    NONE = 0, "不重复"
    YEARLY = 1, "每年"
    MONTHLY = 2, "每月"
    WEEKLY = 3, "每周"
    DAILY = 4, "每天"
    HALF_YEARLY = 11, "每半年"
    THREE_MONTHLY = 23, "每3个月"


class ReminderChannel(IntEnumPro):
    "提醒渠道"

    SITE = 1, "站内信"
    EMAIL = 2, "邮件"
    SMS = 3, "短信"


class AttachmentType(IntEnumPro):
    IMAGE = 1, "图片"
    VIDEO = 2, "视频"
    FILE = 3, "文件"
    LINK = 4, "链接"


class CalendarType(IntEnumPro):
    """日历类型"""

    GREGORIAN = 1, "公历"
    LUNAR = 2, "农历"


class GroupRole(IntEnumPro):
    """共享组角色"""

    OWNER = 1, "所有者"
    MEMBER = 2, "成员"


class SettingsGroup(EnumPro):
    """系统设置分组"""

    ACCOUNT = "account", "账号设置"
    GENERIC = "generic", "通用设置"
    NOTIFICATION = "notification", "通知设置"
    PRIVACY = "privacy", "隐私设置"
    OTHER = "other", "其他"


class SettingsSwitch(EnumPro):
    """系统设置开关值"""

    ON = "ON", "开启"
    OFF = "OFF", "关闭"


class InviteState(IntEnumPro):
    """邀请状态"""

    PENDING = 0, "待发送"
    SENT = 1, "已发送"
    ACCEPTED = 2, "已接受"
    DECLINED = 3, "已拒绝"
    EXPIRED = 4, "已过期"
    CANCELLED = 5, "已撤销"


class InviteTargetType(IntEnumPro):
    """邀请目标类型"""


    GROUP = 2, "共享组"


class NtfyState(IntEnumPro):
    """通知状态"""

    SCHEDULED = 0, "待发送"
    SENT = 1, "已送达"
    FAILED = 2, "发送失败"
    CANCELED = 3, "已取消"



class MediaType(IntEnumPro):
    """媒体类型"""

    IMAGE = 1, "图片"
    VIDEO = 2, "视频"
    FILE = 3, "文件"
    LINK = 4, "链接"
    AUDIO = 5, "音频"


class MediaState(IntEnumPro):
    """媒体状态"""

    UNREVIEWED = -1, "待审核"
    FAILED = 0, "审核失败"
    PASSED = 1, "审核通过"


class SysActionEnum(IntEnumPro):
    SYS = 99, "系统"


class SysAnnounceActionEnum(IntEnumPro):
    ANNOUNCE = 98, "公告"



class EmailBizEnum(EnumPro):
    VERIFY_CODE_SIGN = (
        "verify_code_sign",
        "注册验证码",
    )
    VERIFY_CODE_LOGIN = (
        "verify_code_login",
        "登录验证码",
    )
    VERIFY_CODE_SET_PWD = (
        "verify_code_reset_pwd",
        "重置密码验证码",
    )
    VERIFY_CODE_BIND_PHONE = (
        "verify_code_bind_phone",
        "绑定手机号验证码",
    )
    VERIFY_CODE_REVOKE = (
        "verify_code_account_revoke",
        "账号注销验证码",
    )
    INVITE_GROUP = "invite_group", "共享组邀请"



class AccountType(IntEnumPro):
    CASH = 1, "现金"
    BANK = 2, "银行存款"
    PAYMENT = 3, "支付账户"
    CREDIT_CARD = 4, "信用卡"
    SECURITIES = 5, "证券账户"
    WEALTH = 6, "理财账户"
    OTHER = 7, "其他"


class AccountStatus(IntEnumPro):
    NORMAL = 1, "正常"
    FROZEN = 2, "冻结"
    CLOSED = 3, "关闭"


class CategoryType(IntEnumPro):
    INCOME = 1, "收入"
    EXPENSE = 2, "支出"
    ASSET = 3, "资产"
    LIABILITY = 4, "负债"
    OTHER = 5, "其他"


class TransactionType(IntEnumPro):
    INCOME = 1, "收入"
    EXPENSE = 2, "支出"
    TRANSFER = 3, "转账"
    BORROW_IN = 4, "借入"
    BORROW_OUT = 5, "借出"
    REPAYMENT = 6, "还款"
    ADJUST = 7, "调整"


class TransactionStatus(IntEnumPro):
    NORMAL = 1, "正常"
    REVOKED = 2, "撤销"


class AssetType(IntEnumPro):
    REAL_ESTATE = 1, "房产"
    VEHICLE = 2, "车辆"
    COLLECTIBLE = 3, "收藏品"
    CAMERA = 5, "相机"
    MOBILE = 6, "手机"
    SHOE = 7, "鞋"
    DRESS = 8, "服装"
    JEWELRY = 9, "珠宝"
    OTHER_DIGITAL = 10, "其他数码"
    OTHER = 4, "其他"
    



class AssetValuationMethod(IntEnumPro):
    """估值方式"""

    MANUAL = 1, "手动"
    MARKET = 2, "市场"
    ESTIMATE = 3, "估算"


class AssetStatus(IntEnumPro):
    NORMAL = 1, "正常"
    SOLD = 2, "已出售"
    FROZEN = 3, "冻结"


class AssetValuationSource(IntEnumPro):
    MANUAL = 1, "手动"
    IMPORT = 2, "导入"
    SYSTEM = 3, "系统"


class LiabilityType(IntEnumPro):
    CREDIT_CARD = 1, "信用卡欠款"
    MORTGAGE = 2, "房贷"
    CAR_LOAN = 3, "车贷"
    CONSUMER_LOAN = 4, "消费贷"
    FRIEND_LOAN = 5, "亲友借款"
    OTHER = 6, "其他"


class RepaymentType(IntEnumPro):
    EQUAL_INSTALLMENT = 1, "等额本息"
    EQUAL_PRINCIPAL = 2, "等额本金"
    BULLET = 3, "到期一次性"
    OTHER = 4, "其他"


class LiabilityStatus(IntEnumPro):
    ACTIVE = 1, "生效"
    SETTLED = 2, "已结清"
    VOID = 3, "已作废"


class HoldingType(IntEnumPro):
    STOCK = 1, "股票"
    FUND = 2, "基金"
    ETF = 3, "ETF"
    BOND = 4, "债券"
    GOLD = 5, "黄金"
    DIGITAL = 6, "数字资产"
    OTHER = 7, "其他"


class HoldingStatus(IntEnumPro):
    NORMAL = 1, "正常"
    FROZEN = 2, "冻结"
    CLEARED = 3, "已清仓"


class GoalType(IntEnumPro):
    EMERGENCY = 1, "应急金"
    TRAVEL = 2, "旅行基金"
    HOUSE_DOWN_PAYMENT = 3, "买房首付"
    CAR_FUND = 4, "买车基金"
    EARLY_REPAYMENT = 5, "提前还贷"
    EDUCATION = 6, "教育金"
    RETIREMENT = 7, "退休金"
    OTHER = 8, "其他"


class GoalStatus(IntEnumPro):
    IN_PROGRESS = 1, "进行中"
    COMPLETED = 2, "已完成"
    PAUSED = 3, "已暂停"


class ReminderType(IntEnumPro):
    REPAYMENT = 1, "还款提醒"
    DCA = 2, "定投提醒"
    SALARY = 3, "工资入账提醒"
    TARGET_SAVING = 4, "目标储蓄提醒"
    CERTIFICATE_EXPIRY = 5, "证件/保险到期提醒"
    VALUATION_UPDATE = 6, "估值更新提醒"
    OTHER = 7, "其他"


class RelatedObjectType(IntEnumPro):
    ACCOUNT = 1, "账户"
    ASSET = 2, "资产"
    LIABILITY = 3, "负债"
    GOAL = 4, "目标"
    TRANSACTION = 5, "交易"
    OTHER = 6, "其他"


class ScheduleType(IntEnumPro):
    ONCE = 1, "一次性"
    RECURRING = 2, "周期性"


class ReminderStatus(IntEnumPro):
    ENABLED = 1, "启用"
    DISABLED = 2, "停用"


class TagStatus(IntEnumPro):
    ENABLED = 1, "启用"
    DISABLED = 2, "停用"


class ExchangeRateSource(IntEnumPro):
    MANUAL = 1, "手动"
    SYSTEM = 2, "系统"
    IMPORT = 3, "导入"


class AuditActionType(IntEnumPro):
    CREATE = 1, "创建"
    UPDATE = 2, "更新"
    DELETE = 3, "删除"
    ENABLE = 4, "启用"
    DISABLE = 5, "停用"
    IMPORT = 6, "导入"
    EXPORT = 7, "导出"
    LOGIN = 8, "登录"
    LOGOUT = 9, "登出"
    OTHER = 99, "其他"


class AuditObjectType(IntEnumPro):
    ACCOUNT = 1, "账户"
    ASSET = 2, "资产"
    LIABILITY = 3, "负债"
    TRANSACTION = 4, "交易"
    GOAL = 5, "目标"
    REMINDER = 6, "提醒"
    OTHER = 7, "其他"


class JobType(IntEnumPro):
    IMPORT = 1, "导入"
    EXPORT = 2, "导出"


class ModuleType(IntEnumPro):
    ASSET = 1, "资产"
    TRANSACTION = 2, "流水"
    LIABILITY = 3, "负债"
    GOAL = 4, "目标"
    HOLDING = 5, "持仓"
    OTHER = 6, "其他"


class DataJobStatus(IntEnumPro):
    PROCESSING = 1, "处理中"
    SUCCESS = 2, "成功"
    FAILED = 3, "失败"


class RuleType(IntEnumPro):
    TRANSACTION = 1, "周期记账"
    DCA = 2, "定投"
    REMINDER = 3, "周期提醒"
    OTHER = 4, "其他"


class IntervalUnit(IntEnumPro):
    DAY = 1, "天"
    WEEK = 2, "周"
    MONTH = 3, "月"
    YEAR = 4, "年"

