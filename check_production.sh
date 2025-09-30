#!/bin/bash

BASE_URL="https://web-production-4e1b.up.railway.app"

echo "=== 1. Checking Health ==="
curl -s "$BASE_URL/health" | python -m json.tool

echo -e "\n=== 2. Checking Database Status (for duplicates) ==="
curl -s "$BASE_URL/api/debug/database-status" | python -m json.tool

echo -e "\n=== 3. Checking Performance API ==="
curl -s "$BASE_URL/api/performance?period=ALL" | python -m json.tool

echo -e "\n=== 4. Checking Trades API ==="
curl -s "$BASE_URL/api/trades" | python -m json.tool | head -20

echo -e "\n=== 5. Checking Orders API ==="
curl -s "$BASE_URL/api/orders" | python -m json.tool | head -20
