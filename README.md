# Wallet API Service

REST API сервис для управления балансом кошельков.

## Возможности

- **GET** `/api/v1/wallets/{WALLET_UUID}` - получение информации о кошельке и текущем балансе
- **POST** `/api/v1/wallets/{WALLET_UUID}/operation` - выполнение операций DEPOSIT (пополнение) или WITHDRAW (снятие)

## Технологии

- Django 4.2.7
- Django REST Framework
- PostgreSQL
- Docker & Docker Compose

## Установка и запуск

### Требования

- Docker
- Docker Compose

### Запуск проекта

1. Клонируйте репозиторий
2. (Опционально) Создайте файл `.env` на основе `env.example` для настройки переменных окружения:
   ```bash
   cp env.example .env
   ```
   
   Или создайте файл `.env` вручную с нужными значениями. Если файл `.env` не создан, будут использованы значения по умолчанию из `docker-compose.yml`.

3. Запустите проект:
   ```bash
   docker-compose up --build
   ```

4. Приложение будет доступно по адресу: `http://localhost:8000`

## Использование API

### Получение информации о кошельке

```bash
GET /api/v1/wallets/{WALLET_UUID}
```

**Пример ответа:**
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "balance": "1000.00",
    "created_at": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-19T10:30:00Z"
}
```

### Выполнение операции

```bash
POST /api/v1/wallets/{WALLET_UUID}/operation
Content-Type: application/json

{
    "operation_type": "DEPOSIT",
    "amount": 1000
}
```

**Операции:**
- `DEPOSIT` - пополнение баланса
- `WITHDRAW` - снятие с баланса

**Пример ответа:**
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "balance": "2000.00",
    "created_at": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-19T10:35:00Z"
}
```

## Особенности реализации

- Использование `select_for_update()` для предотвращения race conditions при конкурентных запросах
- Транзакции для обеспечения атомарности операций
- История операций сохраняется в таблице `WalletOperation`
- Подготовлена структура для будущей версии API v2

## Структура проекта

```
itk_django/
├── wallet_api/          # Основной проект Django
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── wallets/             # Приложение для работы с кошельками
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```


