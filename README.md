# Wallet API Service

REST API service for wallet balance management.

## Features

- JWT-based authentication using Djoser
- **GET** `/api/v1/wallets/{WALLET_UUID}` - get wallet information and current balance
- **POST** `/api/v1/wallets/{WALLET_UUID}/operation` - execute DEPOSIT (add) or WITHDRAW (subtract) operations

## Technologies

- Django 5.2.8
- Django REST Framework
- Djoser (authentication)
- djangorestframework-simplejwt (JWT tokens)
- PostgreSQL
- Docker & Docker Compose

## Installation and Setup

### Requirements

- Docker
- Docker Compose

### Running the Project

1. Clone the repository

2. Create `.env` file based on `env.example` for environment variables:
   ```bash
   cp env.example .env
   ```
   
   Or create `.env` manually with required values.

3. Start the project:
   ```bash
   docker-compose up --build
   ```

4. Application will be available at: `http://localhost:3000`

5. Don't forget to create Django superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```


## API Usage

### Authentication

All API endpoints require JWT authentication. First, obtain an access token:

**Register a new user:**
```bash
POST /api/auth/users/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}
```

**Obtain JWT token:**
```bash
POST /api/auth/token/
Content-Type: application/json

{
    "username": "testuser",
    "password": "testpass123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Refresh token:**
```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Use token in requests:**
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Get Wallet Information

```bash
GET /api/v1/wallets/{WALLET_UUID}
Authorization: Bearer {ACCESS_TOKEN}
```

**Example response:**
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "balance": "1000.00",
    "created_at": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-19T10:30:00Z"
}
```

### Execute Operation

```bash
POST /api/v1/wallets/{WALLET_UUID}/operation
Content-Type: application/json
Authorization: Bearer {ACCESS_TOKEN}

{
    "operation_type": "DEPOSIT",
    "amount": 1000
}
```

**Operations:**
- `DEPOSIT` - add to balance
- `WITHDRAW` - subtract from balance

**Example response:**
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "balance": "2000.00",
    "created_at": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-19T10:35:00Z"
}
```

## Testing

The project includes comprehensive test suite covering all main components:

### Running Tests

**In Docker container:**
```bash
docker-compose exec web python manage.py test
```

**Locally (if database is configured):**
```bash
python manage.py test
```

### Test Coverage

- **Models** (`test_models.py`):
  - Wallet and operation creation
  - Data validation
  - Model relationships
  - Cascade deletion

- **Serializers** (`test_serializers.py`):
  - Operation data validation
  - Operation type validation
  - Amount validation (positive, negative, zero)

- **API Endpoints** (`test_views.py`):
  - GET `/api/v1/wallets/{uuid}` - get wallet
  - POST `/api/v1/wallets/{uuid}/operation` - DEPOSIT and WITHDRAW operations
  - Error handling (404, 400, 405)
  - Input validation
  - Operation sequences

- **Concurrent Operations** (`test_concurrent.py`):
  - Simultaneous DEPOSIT operations
  - Simultaneous WITHDRAW operations
  - Mixed operations
  - Race condition prevention
  - Insufficient balance handling in concurrent requests

### Running Specific Tests

```bash
# All tests
python manage.py test

# Specific test class
python manage.py test wallets.tests.test_views.WalletDetailViewTest

# Specific test
python manage.py test wallets.tests.test_views.WalletDetailViewTest.test_get_existing_wallet

# Verbose output
python manage.py test --verbosity=2
```

## Implementation Details

- JWT-based authentication using Djoser and djangorestframework-simplejwt
- All API endpoints require authentication
- Uses `select_for_update()` to prevent race conditions in concurrent requests
- Transactions ensure operation atomicity
- Operation history stored in `WalletOperation` table
- Structure prepared for future API v2 version
- Comprehensive test coverage for all system components

## Project Structure

```
itk_django/
├── wallet_api/          # Main Django project
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── wallets/             # Wallet management app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```
