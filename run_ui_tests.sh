#!/bin/bash

# UI Test Runner for GrowFolio CMS
# Runs tests and monitors server logs

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                  GrowFolio CMS - UI Test Suite Runner                     ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if server is running
if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Server is not running on port 8000${NC}"
    echo -e "${YELLOW}Please start the server with: python -m uvicorn main:app --reload${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Server is running on port 8000${NC}"
echo ""

# Check if playwright is installed
if ! python -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Playwright not installed. Installing...${NC}"
    pip install playwright pytest-playwright
    playwright install
fi

echo -e "${BLUE}🧪 Running UI tests...${NC}"
echo ""

# Run tests with pytest
pytest tests/test_ui.py -v --tb=short --html=test_report.html --self-contained-html

# Capture exit code
EXIT_CODE=$?

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "║  ${GREEN}✅ All tests passed!${NC}                                                      ║"
else
    echo -e "║  ${RED}❌ Some tests failed. Check the output above.${NC}                            ║"
fi
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}📊 Test report generated: test_report.html${NC}"
echo ""

exit $EXIT_CODE
