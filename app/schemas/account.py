from pydantic import BaseModel

from app.constant import AccountStatus, AccountType
from app.schemas.common import EntityModel



class CreateAccountSchema(BaseModel):
    account_type: int
    name: str
    currency: str = "CNY"
    balance: int = 0


class UpdateAccountSchema(BaseModel):
    name: str | None = None
    balance: int | None = None
    status: int | None = None


class AccountListSchema(EntityModel):
    id: str
    account_type: AccountType
    name: str
    currency: str
    balance: int
    status: AccountStatus


class AccountDetailSchema(EntityModel):
    available_balance: int
    credit_limit: int | None = None
    note: str | None = None