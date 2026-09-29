#!/usr/bin/env python3

"""
识别“支出后退款”的冲减交易，并将双方 transaction_type 标记为 8。

匹配规则：
1. 指定 user_id
2. merchant 相同
3. 支出 amount < 0
4. 退款 amount > 0
5. 金额绝对值相同
6. 退款发生在支出之后
7. 默认间隔 <= 45 天，可通过 --max-days 修改
8. transaction_type != 8
9. deleted_id = '0'
10. 一笔支出最多匹配一笔退款
11. 一笔退款最多匹配一笔支出
12. 退款优先匹配最近的一笔尚未被匹配的支出

数据库配置读取项目 .env：

DB_MAIN_URL=postgresql+asyncpg://postgres:123456@127.0.0.1:5432/networthlens

依赖：

pip install sqlalchemy asyncpg python-dotenv

使用：

# dry-run（默认）
python scripts/mark_offset_transactions.py --user-id 123456

# 显式 dry-run
python scripts/mark_offset_transactions.py --user-id 123456 --dry-run

# 指定 45 天
python scripts/mark_offset_transactions.py --user-id 123456 --max-days 45 --dry-run

# 确认后正式更新
python scripts/mark_offset_transactions.py --user-id 123456 --max-days 45 --apply
"""

import argparse
import asyncio
import os

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import load_env as env_loader
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import create_async_engine


# ============================================================
# 配置
# ============================================================

# “冲减” transaction_type 枚举值
OFFSET_TRANSACTION_TYPE = 8

# 默认允许退款与原支出的最大间隔
DEFAULT_MAX_DAYS = 30


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Transaction:
    id: str
    transaction_id: str
    user_id: int
    transaction_type: int
    merchant: str | None
    product: str | None
    amount: int
    occurred_at: datetime


@dataclass
class Match:
    expense: Transaction
    refund: Transaction


# ============================================================
# 命令行参数
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="识别并标记冲减交易"
    )

    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
        help="需要处理的 user_id",
    )

    parser.add_argument(
        "--max-days",
        type=int,
        default=DEFAULT_MAX_DAYS,
        help=(
            "支出与退款允许的最大间隔天数，"
            f"默认 {DEFAULT_MAX_DAYS} 天"
        ),
    )

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="只识别并打印结果，不修改数据库（默认）",
    )

    mode.add_argument(
        "--apply",
        action="store_true",
        help="将匹配交易的 transaction_type 更新为 8",
    )

    args = parser.parse_args()

    if args.max_days <= 0:
        parser.error("--max-days 必须大于 0")

    return args


# ============================================================
# 数据库查询
# ============================================================

async def load_transactions(
    conn,
    user_id: int,
) -> list[Transaction]:
    """
    加载指定用户所有可能参与冲减匹配的交易。

    排除：
    - transaction_type = 8
    - 已删除
    - merchant IS NULL
    - amount = 0
    """

    sql = text(
        """
        SELECT
            id,
            transaction_id,
            user_id,
            transaction_type,
            merchant,
            product,
            amount,
            occurred_at
        FROM "transaction"
        WHERE user_id = :user_id
          AND transaction_type <> :offset_type
          AND deleted_id = '0'
          AND merchant IS NOT NULL
          AND amount <> 0
        ORDER BY occurred_at ASC, id ASC
        """
    )

    result = await conn.execute(
        sql,
        {
            "user_id": user_id,
            "offset_type": OFFSET_TRANSACTION_TYPE,
        },
    )

    transactions: list[Transaction] = []

    for row in result:
        transactions.append(
            Transaction(
                id=row.id,
                transaction_id=row.transaction_id,
                user_id=row.user_id,
                transaction_type=row.transaction_type,
                merchant=row.merchant,
                product=row.product,
                amount=row.amount,
                occurred_at=row.occurred_at,
            )
        )

    return transactions


# ============================================================
# 冲减识别
# ============================================================

def find_matches(
    transactions: list[Transaction],
    max_days: int,
) -> list[Match]:
    """
    严格一对一匹配。

    处理方式：

    按 occurred_at 从早到晚扫描交易。

    遇到支出：
        放入“尚未退款”的集合。

    遇到退款：
        根据 merchant + amount 找之前的支出。

        如果存在多笔相同支出，则优先匹配时间最近的一笔。

    匹配成功后：
        立即从未匹配集合移除该支出。

    因此保证：
        一笔支出只能被匹配一次。
        一笔退款只能匹配一笔支出。
    """

    max_interval = timedelta(days=max_days)

    # key:
    #
    # (
    #     merchant,
    #     abs(amount)
    # )
    #
    # value:
    #
    # 尚未被退款匹配的支出
    #
    # list 按 occurred_at 从早到晚排列
    unmatched_expenses: dict[
        tuple[str, int],
        list[Transaction]
    ] = defaultdict(list)

    matches: list[Match] = []

    for tx in transactions:

        if not tx.merchant:
            continue

        # ====================================================
        # 支出
        # ====================================================

        if tx.amount < 0:

            key = (
                tx.merchant,
                abs(tx.amount),
            )

            unmatched_expenses[key].append(tx)

            continue

        # ====================================================
        # 退款
        # ====================================================

        if tx.amount > 0:

            key = (
                tx.merchant,
                tx.amount,
            )

            expenses = unmatched_expenses.get(key)

            if not expenses:
                continue

            matched_index: int | None = None

            # 从最后面开始找
            #
            # 即优先匹配最近发生的一笔消费
            for index in range(
                len(expenses) - 1,
                -1,
                -1,
            ):
                expense = expenses[index]

                interval = (
                    tx.occurred_at
                    - expense.occurred_at
                )

                # 理论上 transactions 已经按照时间排序，
                # 一般不会出现 < 0。
                if interval < timedelta(0):
                    continue

                # 45 天以内
                if interval <= max_interval:
                    matched_index = index
                    break

                # 当前已经超过 45 天。
                #
                # 因为更前面的 expense 时间只会更早，
                # 所以也一定超过 max_days。
                break

            # 没找到合适支出
            if matched_index is None:
                continue

            # 从未匹配支出中删除
            expense = expenses.pop(matched_index)

            matches.append(
                Match(
                    expense=expense,
                    refund=tx,
                )
            )

    return matches


# ============================================================
# 输出
# ============================================================

def format_amount(amount: int) -> str:
    """
    假设 amount 单位是“分”。

    例如：
        -9999 -> -99.99

    如果数据库 amount 本身就是元，
    可以改成：
        return str(amount)
    """

    return f"{amount / 100:.2f}"


def print_matches(
    matches: list[Match],
    max_days: int,
):
    print()
    print("=" * 110)

    if not matches:
        print(
            f"没有发现符合条件的冲减交易"
            f"（最大间隔 {max_days} 天）"
        )
        print("=" * 110)
        return

    print(
        f"发现 {len(matches)} 组冲减交易"
        f"（最大间隔 {max_days} 天）"
    )

    print("=" * 110)

    for index, match in enumerate(matches, start=1):

        expense = match.expense
        refund = match.refund

        interval = (
            refund.occurred_at
            - expense.occurred_at
        )

        print()
        print(f"[{index}]")
        print(f"user_id  : {expense.user_id}")
        print(f"merchant : {expense.merchant}")

        print()
        print("支出：")

        print(
            f"  id             = {expense.id}"
        )

        print(
            f"  transaction_id = "
            f"{expense.transaction_id}"
        )

        print(
            f"  product        = "
            f"{expense.product or '-'}"
        )

        print(
            f"  amount         = "
            f"{format_amount(expense.amount)} "
            f"({expense.amount})"
        )

        print(
            f"  occurred_at    = "
            f"{expense.occurred_at}"
        )

        print()
        print("退款：")

        print(
            f"  id             = {refund.id}"
        )

        print(
            f"  transaction_id = "
            f"{refund.transaction_id}"
        )

        print(
            f"  product        = "
            f"{refund.product or '-'}"
        )

        print(
            f"  amount         = "
            f"{format_amount(refund.amount)} "
            f"({refund.amount})"
        )

        print(
            f"  occurred_at    = "
            f"{refund.occurred_at}"
        )

        print()

        print(
            f"时间间隔 : {interval}"
        )

        print("-" * 110)

    print()

    print(
        f"匹配：{len(matches)} 组"
    )

    print(
        f"涉及：{len(matches) * 2} 笔交易"
    )

    print("=" * 110)


# ============================================================
# 更新数据库
# ============================================================

async def apply_matches(
    conn,
    user_id: int,
    matches: list[Match],
) -> int:
    """
    将匹配成功的支出 + 退款统一更新：

        transaction_type = 8

    同时再次限制：
        user_id
        transaction_type != 8
        deleted_id = '0'
    """

    if not matches:
        return 0

    ids: list[str] = []

    for match in matches:
        ids.append(match.expense.id)
        ids.append(match.refund.id)

    # 去重
    ids = list(set(ids))

    stmt = (
        text(
            """
            UPDATE "transaction"
            SET
                transaction_type = :offset_type,
                utime = NOW()
            WHERE user_id = :user_id
              AND id IN :ids
              AND transaction_type <> :offset_type
              AND deleted_id = '0'
            """
        )
        .bindparams(
            bindparam(
                "ids",
                expanding=True,
            )
        )
    )

    result = await conn.execute(
        stmt,
        {
            "offset_type": OFFSET_TRANSACTION_TYPE,
            "user_id": user_id,
            "ids": ids,
        },
    )

    return result.rowcount


# ============================================================
# 主程序
# ============================================================

async def main():
    args = parse_args()

    # --------------------------------------------------------
    # 默认 dry-run
    #
    # 只有明确传入 --apply 才会修改数据库。
    # --------------------------------------------------------

    dry_run = not args.apply

    # --------------------------------------------------------
    # 加载 .env
    # --------------------------------------------------------

    env_loader.load_env()

    database_url = os.getenv("DB_MAIN_URL")

    if not database_url:
        raise RuntimeError(
            "未找到环境变量 DB_MAIN_URL，请检查项目 .env 文件"
        )

    # --------------------------------------------------------
    # 创建 Async SQLAlchemy Engine
    # --------------------------------------------------------

    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    try:

        async with engine.connect() as conn:

            print()
            print("=" * 110)
            print("冲减交易识别")
            print("=" * 110)

            print(
                f"user_id              : {args.user_id}"
            )

            print(
                f"max_days             : {args.max_days}"
            )

            print(
                f"offset transaction   : "
                f"{OFFSET_TRANSACTION_TYPE}"
            )

            print(
                f"mode                 : "
                f"{'DRY-RUN' if dry_run else 'APPLY'}"
            )

            # ------------------------------------------------
            # 查询数据
            # ------------------------------------------------

            transactions = await load_transactions(
                conn,
                args.user_id,
            )

            print()
            print(
                f"加载候选交易：{len(transactions)} 笔"
            )

            # ------------------------------------------------
            # 匹配
            # ------------------------------------------------

            matches = find_matches(
                transactions,
                max_days=args.max_days,
            )

            # ------------------------------------------------
            # 输出
            # ------------------------------------------------

            print_matches(
                matches,
                max_days=args.max_days,
            )

            # ------------------------------------------------
            # DRY-RUN
            # ------------------------------------------------

            if dry_run:

                print()
                print(
                    "DRY-RUN：数据库未发生任何修改。"
                )

                if matches:
                    print()
                    print(
                        "确认以上结果无误后，可以执行："
                    )

                    print()

                    print(
                        "python scripts/"
                        "mark_offset_transactions.py "
                        f"--user-id {args.user_id} "
                        f"--max-days {args.max_days} "
                        "--apply"
                    )

                return

            # ------------------------------------------------
            # APPLY
            # ------------------------------------------------

            if not matches:
                print()
                print(
                    "没有需要更新的数据。"
                )
                return

            print()
            print(
                "开始更新 transaction_type = 8 ..."
            )

            try:

                updated_count = await apply_matches(
                    conn,
                    user_id=args.user_id,
                    matches=matches,
                )

                # 显式提交事务
                await conn.commit()

            except Exception:

                # UPDATE 出错明确 rollback
                await conn.rollback()

                raise

            print()

            print(
                f"更新成功：{updated_count} 笔交易"
            )

            print(
                f"冲减组数：{len(matches)} 组"
            )

            # 正常情况下：
            #
            # updated_count == len(matches) * 2
            #
            # 如果不相同，需要检查执行期间数据是否发生变化。

            expected_count = len(matches) * 2

            if updated_count != expected_count:

                print()
                print(
                    "WARNING：实际更新数量与预期不一致！"
                )

                print(
                    f"预期更新：{expected_count}"
                )

                print(
                    f"实际更新：{updated_count}"
                )

                print(
                    "可能有交易在脚本执行期间被其他程序修改。"
                )

    finally:

        await engine.dispose()


# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())