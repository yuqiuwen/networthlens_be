#!/usr/bin/env bash

set -u

API_URL="${API_URL:-http://localhost:8080/v1/transaction}"
TOKEN="${TOKEN:-}"
CSV_FILE="${1:-transactions.csv}"

if [[ ! -f "$CSV_FILE" ]]; then
    echo "CSV 文件不存在: $CSV_FILE"
    exit 1
fi

if [[ -z "$TOKEN" ]]; then
    echo "请设置 TOKEN 环境变量"
    echo "例如："
    echo "TOKEN='xxx' ./import_transactions.sh transactions.csv"
    exit 1
fi

success=0
failed=0
total=0

# Python 负责：
# 1. 正确解析 CSV
# 2. 跳过表头
# 3. 空字符串转换为 null
# 4. amount/channel/transaction_type 转换为数字
# 5. 输出单行 JSON
while IFS= read -r json; do
    curl -sS \
        -X POST "$API_URL" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        --data-raw "$json"

    echo
done < <(
    python3 - "$CSV_FILE" <<'PY'
import csv
import json
import sys

filename = sys.argv[1]

def nullable(value):
    if value is None:
        return None
    value = value.strip()
    return value if value else None

def integer(value):
    value = nullable(value)
    return int(value) if value is not None else None

with open(filename, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if not any(value and value.strip() for value in row.values()):
            continue

        data = {
            "category_id": nullable(row["category_id"]),
            "occurred_at": nullable(row["occurred_at"]),
            "amount": integer(row["amount"]),
            "source_account_id": nullable(row["source_account_id"]),
            "target_account_id": nullable(row["target_account_id"]),
            "product": nullable(row["product"]),
            "note": nullable(row["note"]),
            "merchant": nullable(row["merchant"]),
            "channel": integer(row["channel"]),
            "transaction_type": integer(row["transaction_type"]),
        }

        print(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
PY
)

echo
echo "=============================="
echo "导入完成"
echo "总计: $total"
echo "成功: $success"
echo "失败: $failed"
echo "=============================="

if [[ $failed -gt 0 ]]; then
    exit 1
fi