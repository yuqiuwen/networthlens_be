from pydantic import BaseModel, Field

from app.constant import AccountStatus, AccountType
from app.schemas.common import EntityModel



class CreateAccountSchema(BaseModel):
    account_type: int
    name: str
    currency: str = "CNY"
    balance: int = 0
    note: str | None = Field(default=None, max_length=100)
    icon: str | None = Field(default=None)


class UpdateAccountSchema(BaseModel):
    name: str | None = None
    balance: int | None = None
    status: int | None = None
    note: str | None = Field(default=None, max_length=100)
    icon: str | None = Field(default=None)


class AccountListSchema(EntityModel):
    id: str
    account_type: AccountType
    name: str
    currency: str
    balance: int
    status: AccountStatus
    note: str | None
    icon: str | None



class AccountDetailSchema(EntityModel):
    available_balance: int
    credit_limit: int | None = None
    note: str | None = None
    icon: str | None