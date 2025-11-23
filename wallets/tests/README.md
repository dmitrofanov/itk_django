# Тесты для приложения wallets

## Структура тестов

### test_models.py
Тесты для моделей `Wallet` и `WalletOperation`:
- Создание объектов
- Валидация данных
- Связи между моделями
- Каскадное удаление

### test_serializers.py
Тесты для сериализаторов:
- `WalletSerializer` - сериализация кошельков
- `WalletOperationSerializer` - валидация операций
- Проверка всех граничных случаев

### test_views.py
Тесты для API endpoints:
- **GET** `/api/v1/wallets/{uuid}` - получение информации о кошельке
- **POST** `/api/v1/wallets/{uuid}/operation` - выполнение операций
- Обработка всех типов ошибок
- Валидация входных данных
- Проверка структуры ответов

### test_concurrent.py
Тесты для проверки корректной обработки конкурентных запросов:
- Одновременные операции DEPOSIT
- Одновременные операции WITHDRAW
- Смешанные операции
- Предотвращение race conditions
- Обработка недостаточного баланса

## Запуск тестов

```bash
# Все тесты
python manage.py test wallets.tests

# Конкретный файл
python manage.py test wallets.tests.test_views

# Конкретный тест-класс
python manage.py test wallets.tests.test_views.WalletDetailViewTest

# Конкретный тест
python manage.py test wallets.tests.test_views.WalletDetailViewTest.test_get_existing_wallet

# С подробным выводом
python manage.py test --verbosity=2

# С покрытием кода (требует coverage)
coverage run --source='.' manage.py test wallets.tests
coverage report
```

## Статистика тестов

- **Всего тестов:** ~40+
- **Покрытие:** Модели, Сериализаторы, Views, Конкурентные операции
- **Типы тестов:** Unit, Integration, Concurrent

## Важные тесты

### Тесты конкурентных операций
Особое внимание уделено тестам в `test_concurrent.py`, так как они проверяют критически важную функциональность - предотвращение race conditions при одновременных операциях с балансом.

Эти тесты используют `ThreadPoolExecutor` для симуляции реальных конкурентных запросов и проверяют:
1. Корректность финального баланса
2. Отсутствие потери данных
3. Правильную обработку недостаточного баланса

