#!/bin/bash

# Test Runner Script for MyAwesomeFakeCompany AI Agent
# Provides convenient commands to run different test suites

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}AI Agent Test Runner${NC}"
echo -e "${BLUE}================================${NC}"

# Check if uv is available, otherwise fall back to pip
if command -v uv &> /dev/null; then
    PYTEST_CMD="uv run pytest"
    # Check if pytest is installed
    if ! uv run pytest --version > /dev/null 2>&1; then
        echo -e "${RED}Error: pytest not found${NC}"
        echo -e "${YELLOW}Installing test dependencies...${NC}"
        uv pip install pytest pytest-asyncio pytest-cov pytest-mock
    fi
else
    PYTEST_CMD="python3 -m pytest"
    # Check if pytest is installed
    if ! python3 -m pytest --version > /dev/null 2>&1; then
        echo -e "${RED}Error: pytest not found${NC}"
        echo -e "${YELLOW}Installing test dependencies...${NC}"
        python3 -m pip install pytest pytest-asyncio pytest-cov pytest-mock
    fi
fi

# Parse command line arguments
COMMAND=${1:-all}

case $COMMAND in
    all)
        echo -e "\n${GREEN}Running all tests...${NC}"
        $PYTEST_CMD tests/ src/ -v
        ;;

    quick)
        echo -e "\n${GREEN}Running quick test (no coverage)...${NC}"
        $PYTEST_CMD tests/ src/ -q
        ;;

    coverage)
        echo -e "\n${GREEN}Running tests with coverage...${NC}"
        $PYTEST_CMD tests/ src/ --cov=src --cov-report=term-missing -v
        ;;

    week1)
        echo -e "\n${GREEN}Running Week 1 tests (Tools & Security)...${NC}"
        $PYTEST_CMD \
            src/integrations/zendesk/langgraph_agent/tools/tests/ \
            src/security/tests/ \
            -v
        ;;

    week2)
        echo -e "\n${GREEN}Running Week 2 tests (Nodes)...${NC}"
        $PYTEST_CMD \
            src/integrations/zendesk/langgraph_agent/nodes/tests/ \
            -v
        ;;

    security)
        echo -e "\n${GREEN}Running security tests only...${NC}"
        $PYTEST_CMD src/security/tests/ -v
        ;;

    tools)
        echo -e "\n${GREEN}Running tool tests only...${NC}"
        $PYTEST_CMD src/integrations/zendesk/langgraph_agent/tools/tests/ -v
        ;;

    nodes)
        echo -e "\n${GREEN}Running node tests only...${NC}"
        $PYTEST_CMD src/integrations/zendesk/langgraph_agent/nodes/tests/ -v
        ;;

    critical)
        echo -e "\n${GREEN}Running critical security tests...${NC}"
        echo -e "${YELLOW}Q-LLM Intent Extraction (Most Critical)${NC}"
        $PYTEST_CMD \
            src/integrations/zendesk/langgraph_agent/nodes/tests/test_intent_extraction_node.py \
            -v
        ;;

    failed)
        echo -e "\n${GREEN}Re-running failed tests...${NC}"
        $PYTEST_CMD --lf -v
        ;;

    watch)
        echo -e "\n${GREEN}Watching for changes and re-running tests...${NC}"
        echo -e "${YELLOW}Note: Requires pytest-watch (pip install pytest-watch)${NC}"
        ptw -- -v
        ;;

    html)
        echo -e "\n${GREEN}Generating HTML coverage report...${NC}"
        $PYTEST_CMD tests/ src/ --cov=src --cov-report=html
        echo -e "${GREEN}Report generated at: htmlcov/index.html${NC}"
        ;;

    help)
        echo ""
        echo "Usage: ./run_tests.sh [command]"
        echo ""
        echo "Commands:"
        echo "  all       - Run all tests (default)"
        echo "  quick     - Run all tests without coverage (fast)"
        echo "  coverage  - Run all tests with coverage report"
        echo "  week1     - Run Week 1 tests (tools + security)"
        echo "  week2     - Run Week 2 tests (nodes)"
        echo "  security  - Run security tests only"
        echo "  tools     - Run tool tests only"
        echo "  nodes     - Run node tests only"
        echo "  critical  - Run critical security tests (Q-LLM)"
        echo "  failed    - Re-run only failed tests"
        echo "  watch     - Watch for changes and re-run"
        echo "  html      - Generate HTML coverage report"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh               # Run all tests"
        echo "  ./run_tests.sh coverage      # Run with coverage"
        echo "  ./run_tests.sh critical      # Run critical tests only"
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Tests Complete!${NC}"
echo -e "${GREEN}================================${NC}"
