# Testing Guide - Digital FTE Customer Success Agent

Complete testing documentation for the Digital FTE project.

## Table of Contents

1. [Test Overview](#test-overview)
2. [Running Tests](#running-tests)
3. [Test Structure](#test-structure)
4. [Code Coverage](#code-coverage)
5. [Test Categories](#test-categories)
6. [Writing Tests](#writing-tests)

## Test Overview

### Test Statistics

**Total Test Files**: 9
- Unit Tests: 6 files
- Integration Tests: 4 files

**Test Coverage Target**: > 80%

### Test Framework

- **Framework**: pytest 7.4.3
- **Async Support**: pytest-asyncio 0.21.1
- **Coverage**: pytest-cov 4.1.0
- **Mocking**: pytest-mock 3.12.0

## Running Tests

### Quick Start

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Run all tests with coverage
./run_tests.sh

# Run specific test type
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh web
./run_tests.sh gmail
./run_tests.sh whatsapp
./run_tests.sh cross-channel
```

### Manual pytest Commands

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_validators.py -v

# Run specific test function
pytest tests/unit/test_validators.py::TestEmailValidation::test_validate_email_valid -v

# Run with coverage
pytest tests/ --cov=backend/src --cov-report=html -v

# Run tests matching pattern
pytest tests/ -k "email" -v
```

### Test Markers

Tests are organized with markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio

# Run channel-specific tests
pytest -m channel

# Run cross-channel tests
pytest -m cross_channel
```

## Test Structure

```
backend/tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_models.py              # Pydantic model validation
│   ├── test_validators.py          # Custom validators
│   ├── test_gmail_handler.py       # Gmail handler unit tests
│   ├── test_whatsapp_handler.py    # WhatsApp handler unit tests
│   └── test_customer_linking.py    # Customer linking utilities
├── integration/
│   ├── __init__.py
│   ├── test_web_flow.py            # Web form E2E tests
│   ├── test_gmail_flow.py          # Gmail E2E tests
│   ├── test_whatsapp_flow.py       # WhatsApp E2E tests
│   └── test_cross_channel.py       # Cross-channel tests
└── conftest.py                     # Shared fixtures (if needed)
```

## Code Coverage

### Generating Coverage Reports

```bash
# Generate all coverage reports
pytest tests/ \
    --cov=backend/src \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    -v
```

### Coverage Report Types

1. **Terminal Report**: Displayed after test run
   ```
   Name                             Stmts   Miss  Cover   Missing
   --------------------------------------------------------------
   backend/src/agent/prompts.py        45      2    95%   102-103
   backend/src/utils/validators.py     32      0   100%
   --------------------------------------------------------------
   TOTAL                              1234     89    93%
   ```

2. **HTML Report**: Interactive report
   ```bash
   # Generate and open
   pytest tests/ --cov=backend/src --cov-report=html
   open htmlcov/index.html
   ```

3. **XML Report**: For CI/CD integration
   ```bash
   pytest tests/ --cov=backend/src --cov-report=xml
   ```

### Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| **Models** | > 90% | TBD |
| **Validators** | > 90% | TBD |
| **Handlers** | > 80% | TBD |
| **Agent** | > 80% | TBD |
| **Utilities** | > 85% | TBD |
| **Overall** | > 80% | TBD |

## Test Categories

### 1. Unit Tests

Fast tests with no external dependencies (mocked).

**test_models.py** - Pydantic Models
- ✅ Valid data acceptance
- ✅ Invalid data rejection (ValidationError)
- ✅ Field validation rules
- ✅ Data normalization (email lowercase)
- ✅ Required vs optional fields

**test_validators.py** - Custom Validators
- ✅ Email validation and normalization
- ✅ Phone number normalization (E.164)
- ✅ WhatsApp prefix removal
- ✅ Invalid input rejection
- ✅ Whitespace stripping

**test_gmail_handler.py** - Gmail Handler
- ✅ Pub/Sub message parsing
- ✅ Email content extraction
- ✅ Sender info extraction
- ✅ Email formatting (formal)
- ✅ Gmail API error handling

**test_whatsapp_handler.py** - WhatsApp Handler
- ✅ Twilio signature validation
- ✅ Webhook parsing
- ✅ Phone normalization
- ✅ Message splitting (> 1600 chars)
- ✅ Concise formatting

**test_customer_linking.py** - Customer Linking
- ✅ Phone normalization (various formats)
- ✅ Fuzzy matching (Levenshtein distance)
- ✅ Customer lookup/creation
- ✅ Identifier linking
- ✅ Cross-channel metadata

### 2. Integration Tests

End-to-end tests with real database and API calls (mocked external services).

**test_web_flow.py** - Web Form Flow
- ✅ Form submission → Database
- ✅ Agent processing
- ✅ Response generation
- ✅ Duplicate handling

**test_gmail_flow.py** - Gmail Flow
- ✅ Pub/Sub webhook → Parse → Agent → Send
- ✅ Email formatting (formal greeting, signature)
- ✅ Duplicate message handling

**test_whatsapp_flow.py** - WhatsApp Flow
- ✅ Twilio webhook → Parse → Agent → Send
- ✅ Concise formatting
- ✅ Message splitting (long responses)
- ✅ Signature validation

**test_cross_channel.py** - Cross-Channel Flow
- ✅ Email → WhatsApp linking
- ✅ Gmail → Web linking
- ✅ All three channels linking
- ✅ Customer history retrieval
- ✅ > 95% accuracy validation

## Writing Tests

### Unit Test Example

```python
import pytest
from pydantic import ValidationError


class TestMyModel:
    """Test MyModel Pydantic model."""

    def test_valid_data(self):
        """Test model with valid data."""
        from backend.src.models.my_model import MyModel

        model = MyModel(field="value")
        assert model.field == "value"

    def test_invalid_data(self):
        """Test that invalid data is rejected."""
        from backend.src.models.my_model import MyModel

        with pytest.raises(ValidationError):
            MyModel(field="invalid")
```

### Integration Test Example

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_end_to_end_flow(test_client, clean_database):
    """Test complete flow from webhook to response."""

    # Mock external API
    with patch('module.external_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = {"success": True}

        # Send request
        response = test_client.post("/endpoint", json={"data": "value"})

        # Assert response
        assert response.status_code == 200

        # Wait for async processing
        await asyncio.sleep(1)

        # Verify database state
        # ...
```

### Fixtures

Create shared fixtures in `conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create test client."""
    from backend.src.api.main import app
    return TestClient(app)


@pytest.fixture
async def clean_database():
    """Clean database before and after test."""
    # Setup
    await cleanup_test_data()

    yield

    # Teardown
    await cleanup_test_data()
```

## Best Practices

### DO:
✅ Write tests before implementation (TDD)
✅ Test one thing per test function
✅ Use descriptive test names
✅ Mock external services (APIs, databases in unit tests)
✅ Clean up test data after tests
✅ Use fixtures for shared setup
✅ Test both success and failure cases
✅ Test edge cases and boundary conditions
✅ Keep tests independent (no dependencies between tests)

### DON'T:
❌ Test implementation details (test behavior, not internals)
❌ Write tests that depend on execution order
❌ Leave test data in database
❌ Skip tests (fix them instead)
❌ Write slow unit tests (mock external calls)
❌ Test third-party library code
❌ Hardcode values (use fixtures or constants)

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=backend/src --cov-report=xml -v

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./backend/coverage.xml
```

## Troubleshooting

### Common Issues

**1. Import Errors**
```
ModuleNotFoundError: No module named 'backend'
```
**Solution**: Run tests from backend directory or set PYTHONPATH

**2. Database Connection Errors**
```
asyncpg.exceptions.ConnectionDoesNotExistError
```
**Solution**: Ensure PostgreSQL is running and DATABASE_URL is set

**3. Async Test Issues**
```
RuntimeError: no running event loop
```
**Solution**: Use `@pytest.mark.asyncio` decorator and pytest-asyncio

**4. Mock Not Working**
```
AssertionError: Expected mock to be called
```
**Solution**: Check import paths match exactly (use `from module import function`)

### Debug Tips

```bash
# Run tests with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show locals in traceback
pytest -l

# Run with pdb debugger on failure
pytest --pdb
```

## Test Maintenance

### Regular Tasks

- [ ] Review and update tests when code changes
- [ ] Keep coverage > 80%
- [ ] Remove obsolete tests
- [ ] Update mocks when external APIs change
- [ ] Run full test suite before deployment

### Test Health Metrics

- **Test Count**: Track as codebase grows
- **Coverage**: Maintain > 80%
- **Execution Time**: Keep unit tests < 1s each
- **Failure Rate**: Investigate frequent failures

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
