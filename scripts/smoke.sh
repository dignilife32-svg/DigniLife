#!/usr/bin/env bash
set -euo pipefail

BASE=http://localhost:8080
HEAD='-H x-user-id:demo'

echo "1) Health..."
curl -sf $BASE/health/ok >/dev/null
curl -sf $BASE/health/ready >/dev/null
echo "   OK"

echo "2) Wallet summary (FX/locale auto)..."
curl -sf $BASE/wallet/summary $HEAD | jq

echo "3) Withdraw guard..."
curl -s -X POST $BASE/withdraw $HEAD -H "X-Device-Id:new-1" -d 'amount=500' | jq
curl -s -X POST $BASE/withdraw $HEAD -H "X-Device-Id:known-1" -d 'amount=20' | jq

echo "4) Daily earn flow..."
curl -s -X POST "$BASE/earn/daily/bundle/start?minutes=60" $HEAD | jq
sleep 2
curl -s -X POST $BASE/earn/daily/bundle/submit $HEAD | jq
curl -s $BASE/wallet/summary $HEAD | jq '.balance'
