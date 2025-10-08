# Testing Guide

This guide explains how to set up and run tests for the MyAwesomeFakeCompany AI Agent.

## Quick Start

```bash
# 1. Navigate to backend directory
cd backend

# 2. Install test dependencies
pip install -r requirements-test.txt

# 3. Run all tests
pytest

# 4. Run with coverage
pytest --cov=src --cov-report=term-missing
```

---

## Setup

### Prerequisites

- Python 3.12+ installed
- Virtual environment recommended

### Install Test Dependencies

```bash
# Option 1: Using pip
pip install -r requirements-test.txt

# Option 2: Install individually
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Option 3: Using uv (if available)
uv pip install -r requirements-test.txt
```

### Verify Installation

```bash
pytest --version
# Should output: pytest 7.4.0 or higher
```

---

## Running Tests

### Run All Tests

```bash
# From backend directory
pytest

# Or specify paths
pytest tests/ src/
```

### Run Specific Test Files

```bash
# Week 1: Tool tests
pytest src/integrations/zendesk/langgraph_agent/tools/tests/test_zendesk_tools.py

# Week 1: Security tests
pytest src/security/tests/test_pattern_detector.py

# Week 2: Q-LLM tests (most critical)
pytest src/integrations/zendesk/langgraph_agent/nodes/tests/test_intent_extraction_node.py

# Week 2: Supervisor tests
pytest src/integrations/zendesk/langgraph_agent/nodes/tests/test_supervisor_node.py
```

### Run by Test Class

```bash
# Run a specific test class
pytest src/security/tests/test_pattern_detector.py::TestPromptInjectionDetection

# Run a specific test method
pytest src/security/tests/test_pattern_detector.py::TestPromptInjectionDetection::test_detect_ignore_instructions_pattern
```

### Run by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only async tests
pytest -m asyncio

# Run only LLM-related tests
pytest -m llm
```

### Run with Verbose Output

```bash
# Show test names as they run
pytest -v

# Show even more detail
pytest -vv

# Show print statements
pytest -s
```

---

## Coverage Reports

### Basic Coverage

```bash
# Show coverage in terminal
pytest --cov=src

# Show missing lines
pytest --cov=src --cov-report=term-missing

# Show coverage percentage for each file
pytest --cov=src --cov-report=term
```

### HTML Coverage Report

```bash
# Generate HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Coverage by Module

```bash
# Tools coverage
pytest --cov=src/integrations/zendesk/langgraph_agent/tools

# Security coverage
pytest --cov=src/security

# Nodes coverage
pytest --cov=src/integrations/zendesk/langgraph_agent/nodes
```

---

## Performance Testing

### Run Tests with Timing

```bash
# Show slowest 10 tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4

# Run with auto-detection of CPU cores
pytest -n auto
```

---

## Test Organization

### Current Test Structure

```
backend/
├── tests/
│   └── conftest.py                    # Root fixtures
├── src/
│   ├── integrations/zendesk/langgraph_agent/
│   │   ├── tools/tests/
│   │   │   ├── conftest.py           # Tool fixtures
│   │   │   ├── test_awesome_company_tools.py    # Knowledge base (Week 1)
│   │   │   └── test_zendesk_tools.py            # Ticket tools (Week 1)
│   │   └── nodes/tests/
│   │       ├── conftest.py           # Node fixtures
│   │       ├── test_intent_extraction_node.py   # Q-LLM (Week 2)
│   │       ├── test_supervisor_node.py          # Routing (Week 2)
│   │       └── test_sales_agent.py              # Agent (Week 2)
│   └── security/tests/
│       ├── conftest.py               # Security fixtures
│       └── test_pattern_detector.py              # Injection detection (Week 1)
```

### Test Counts by Module

```bash
# Count tests by directory
pytest --collect-only | grep "test session starts"

# Week 1 tests
pytest src/integrations/zendesk/langgraph_agent/tools/tests/ --collect-only -q

# Week 2 tests
pytest src/integrations/zendesk/langgraph_agent/nodes/tests/ --collect-only -q

# Security tests
pytest src/security/tests/ --collect-only -q
```

---

## Debugging Tests

### Run Failed Tests Only

```bash
# Run tests that failed last time
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Stop on First Failure

```bash
# Stop immediately on first failure
pytest -x

# Stop after 3 failures
pytest --maxfail=3
```

### Debug Mode

```bash
# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest -l

# Show full diff for assertions
pytest -vv
```

### Run Specific Test with Print Output

```bash
# Show print statements for one test
pytest src/security/tests/test_pattern_detector.py::TestPromptInjectionDetection::test_detect_ignore_instructions_pattern -s -v
```

---

## Continuous Integration

### Run Tests in CI/CD

```bash
# Recommended CI command
pytest --cov=src --cov-report=xml --cov-report=term -v

# With strict markers (fail on unknown markers)
pytest --strict-markers

# With warnings as errors
pytest -W error
```

### Example GitHub Actions Snippet

```yaml
- name: Run Tests
  run: |
    cd backend
    pip install -r requirements-test.txt
    pytest --cov=src --cov-report=xml --cov-report=term -v
```

---

## Test Configuration

### pytest.ini (Optional)

Create `backend/pytest.ini` for project-wide settings:

```ini
[pytest]
# Test discovery patterns
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests src

# Markers
markers =
    unit: Unit tests (fast, mocked)
    integration: Integration tests (slower)
    slow: Slow tests
    llm: Tests requiring LLM mocking

# Coverage settings
addopts =
    --strict-markers
    --cov-report=term-missing
    --durations=10

# Async settings
asyncio_mode = auto
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError"

```bash
# Solution: Install from backend directory
cd backend
pip install -e .

# Or add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Issue: "No module named pytest"

```bash
# Solution: Install pytest
pip install pytest pytest-asyncio
```

### Issue: "fixture 'mock_llm' not found"

```bash
# Solution: Make sure you're running from backend directory
cd backend
pytest
```

### Issue: Tests hang on async functions

```bash
# Solution: Install pytest-asyncio
pip install pytest-asyncio

# Make sure async tests have @pytest.mark.asyncio decorator
```

---

## Performance Benchmarks

**Expected Test Performance:**

- **All Unit Tests:** < 5 seconds
- **Week 1 Tests:** < 2 seconds
- **Week 2 Tests:** < 3 seconds
- **Single Test File:** < 1 second

If tests are slower, check:
1. No real LLM API calls being made (should be mocked)
2. No real database connections
3. No network requests

---

## Test Quality Metrics

### Current Coverage

```bash
# Check current coverage
pytest --cov=src --cov-report=term

# Target coverage by module:
# - Tools: 90%+
# - Security: 95%+
# - Nodes: 85%+
# - Overall: 80%+
```

### Test Count

```bash
# Total tests
pytest --collect-only -q | tail -1

# Expected counts:
# Week 1: ~120 tests
# Week 2: ~40 tests
# Total: ~160 tests
```

---

## Quick Reference

```bash
# Most common commands
pytest                                  # Run all tests
pytest -v                              # Verbose output
pytest -s                              # Show print statements
pytest --cov=src                       # With coverage
pytest -k "test_intent"                # Run tests matching pattern
pytest -m unit                         # Run unit tests only
pytest --lf                            # Run last failed
pytest -x                              # Stop on first failure
pytest --durations=10                  # Show slowest tests
```

---

## Next Steps

After running tests successfully:

1. **Add more tests** for Week 3 (guardrails, routing)
2. **Set up CI/CD** to run tests automatically
3. **Generate coverage reports** regularly
4. **Use LangSmith** for LLM evaluation (optional)

For questions or issues, see:
- `TESTING_PLAN.md` - Complete testing strategy
- Test files - Examples of test patterns
- `conftest.py` files - Available fixtures
