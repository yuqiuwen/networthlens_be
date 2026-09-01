from fastapi import Query, Depends

from app.services.stats import StatsService
from app.constant import AccountStatus, AccountType
from app.core.dependencies import RequireAuthDep, SessionDep
from app.core.http_handler import RespModel, make_response
from app.routers import BaseAPIRouter
from app.schemas.stats import (

    AccountDistribution,
    AssetDistribution,
    CashFlowTrend,
    DashboardQuery,
    DashboardMetrics,
    ExpenseCategoryStatistics,
    WealthTrend,
    
)
from app.services.account import AccountService


router = BaseAPIRouter(prefix="/stats", tags=["stats"])



@router.get("/metrics", summary="指标统计", response_model=RespModel[DashboardMetrics])
async def get_metrics_stats(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: DashboardQuery= Depends()
):
    ret = await StatsService.get_metrics(session, cur_user, query)
    return make_response(data=ret)


@router.get("/expense-category-stats", summary="支出类别统计", response_model=RespModel[ExpenseCategoryStatistics])
async def get_expense_category(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: DashboardQuery= Depends()
):
    ret = await StatsService.get_expense_category(session, cur_user, query)
    return make_response(data=ret)



@router.get("/cash-flow", summary="现金流", response_model=RespModel[CashFlowTrend])
async def get_cash_flow(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: DashboardQuery= Depends()
):
    ret = await StatsService.get_cash_flow(session, cur_user, query)
    return make_response(data=ret)


@router.get("/account-stats", summary="账户统计", response_model=RespModel[AccountDistribution])
async def get_account_stats(
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    ret = await StatsService.get_account_stats(session, cur_user)
    return make_response(data=ret)


@router.get("/asset-category-stats", summary="资产分类统计", response_model=RespModel[AssetDistribution])
async def get_asset_category_stats(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: DashboardQuery= Depends()
):
    ret = await StatsService.get_asset_category_stats(session, cur_user)
    return make_response(data=ret)


@router.get("/wealth-trend", summary="财富趋势", response_model=RespModel[WealthTrend])
async def get_wealth_trend(
    session: SessionDep,
    cur_user: RequireAuthDep,
    query: DashboardQuery= Depends()
):
    ret = await StatsService.get_wealth_trend(session, cur_user, query)
    return make_response(data=ret)

