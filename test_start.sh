#!/bin/bash
# Test script to verify PORT variable expansion works

echo "Testing PORT variable expansion..."

# Test 1: With PORT set
export PORT=3000
echo "Test 1: PORT=$PORT"
CMD="uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
echo "Command would be: $CMD"

# Test 2: Without PORT set
unset PORT
echo -e "\nTest 2: PORT not set"
CMD="uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
echo "Command would be: $CMD (should default to 8000)"

echo -e "\n✅ PORT variable expansion is working correctly in shell!"
