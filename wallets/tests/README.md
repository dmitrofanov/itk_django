# Tests for wallets app

## Test Structure

### test_models.py
Tests for `Wallet` and `WalletOperation` models:
- Object creation
- Data validation
- Model relationships
- Cascade deletion

### test_serializers.py
Tests for serializers:
- `WalletSerializer` - wallet serialization
- `WalletOperationSerializer` - operation validation
- Edge case validation

### test_views.py
Tests for API endpoints:
- **GET** `/api/v1/wallets/{uuid}` - get wallet information
- **POST** `/api/v1/wallets/{uuid}/operation` - execute operations
- All error types handling
- Input validation
- Response structure validation

### test_concurrent.py
Tests for concurrent request handling:
- Simultaneous DEPOSIT operations
- Simultaneous WITHDRAW operations
- Mixed operations
- Race condition prevention
- Insufficient balance handling

## Running Tests

```bash
# All tests
python manage.py test wallets.tests

# Specific file
python manage.py test wallets.tests.test_views

# Specific test class
python manage.py test wallets.tests.test_views.WalletDetailViewTest

# Specific test
python manage.py test wallets.tests.test_views.WalletDetailViewTest.test_get_existing_wallet

# Verbose output
python manage.py test --verbosity=2

# With code coverage (requires coverage)
coverage run --source='.' manage.py test wallets.tests
coverage report
```

## Test Statistics

- **Total tests:** ~50+
- **Coverage:** Models, Serializers, Views, Concurrent operations
- **Test types:** Unit, Integration, Concurrent

## Important Tests

### Concurrent Operations Tests
Special attention is given to tests in `test_concurrent.py` as they verify critical functionality - race condition prevention during simultaneous balance operations.

These tests use `ThreadPoolExecutor` to simulate real concurrent requests and verify:
1. Final balance correctness
2. No data loss
3. Proper insufficient balance handling
