from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.account import AccountService
from app.services.asset import AssetService
from app.services.fin_analysis import FinancialAnalysisService
from app.services.goal import GoalService
from app.services.liability import LiabilityService
from app.services.transaction import TransactionService


@dataclass
class FinAgentDeps:
    session: AsyncSession
    user_id: int
    analysis_service: FinancialAnalysisService
    transaction_service: TransactionService
    # TODO
    reminder_service: any
