#!/bin/bash
# Test runner script for Digital FTE Customer Success Agent

set -e  # Exit on error

echo "================================"
echo "Digital FTE Test Runner"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Activating venv..."
    source venv/bin/activate
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-yes}"

echo "Test Type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo ""

# Function to run tests
run_tests() {
    local test_path=$1
    local description=$2

    echo -e "${GREEN}Running $description...${NC}"

    if [ "$COVERAGE" = "yes" ]; then
        pytest "$test_path" \
            --cov=backend/src \
            --cov-report=term-missing \
            --cov-report=html:htmlcov \
            -v
    else
        pytest "$test_path" -v
    fi

    echo ""
}

# Run tests based on type
case "$TEST_TYPE" in
    unit)
        run_tests "tests/unit/" "Unit Tests"
        ;;

    integration)
        run_tests "tests/integration/" "Integration Tests"
        ;;

    web)
        run_tests "tests/integration/test_web_flow.py" "Web Form Integration Tests"
        ;;

    gmail)
        run_tests "tests/integration/test_gmail_flow.py" "Gmail Integration Tests"
        ;;

    whatsapp)
        run_tests "tests/integration/test_whatsapp_flow.py" "WhatsApp Integration Tests"
        ;;

    cross-channel)
        run_tests "tests/integration/test_cross_channel.py" "Cross-Channel Tests"
        ;;

    all)
        echo -e "${GREEN}Running ALL Tests${NC}"
        echo ""

        # Run unit tests first
        echo -e "${GREEN}[1/2] Unit Tests${NC}"
        pytest tests/unit/ -v

        echo ""
        echo -e "${GREEN}[2/2] Integration Tests${NC}"
        pytest tests/integration/ -v

        echo ""
        echo -e "${GREEN}Generating Coverage Report${NC}"
        if [ "$COVERAGE" = "yes" ]; then
            pytest tests/ \
                --cov=backend/src \
                --cov-report=term-missing \
                --cov-report=html:htmlcov \
                --cov-report=xml:coverage.xml \
                -v
        fi
        ;;

    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [test-type] [coverage]"
        echo ""
        echo "Test types:"
        echo "  all           - Run all tests (default)"
        echo "  unit          - Run only unit tests"
        echo "  integration   - Run only integration tests"
        echo "  web           - Run web form tests"
        echo "  gmail         - Run Gmail tests"
        echo "  whatsapp      - Run WhatsApp tests"
        echo "  cross-channel - Run cross-channel tests"
        echo ""
        echo "Coverage:"
        echo "  yes  - Generate coverage report (default)"
        echo "  no   - Skip coverage"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"

    if [ "$COVERAGE" = "yes" ]; then
        echo ""
        echo "Coverage report generated:"
        echo "  - Terminal: See above"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
    fi
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
