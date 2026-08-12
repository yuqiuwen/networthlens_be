from pydantic import BaseModel


class AgentResponse(BaseModel):
    answer: str


class CreateExpenseRecordResult(BaseModel):
    success: bool

    transaction_id: str | None = None


class CreateReminderResult(BaseModel):
    success: bool

    reminder_id: str | None = None