from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from wallets.models import Wallet
from wallets.serializers import (
    WalletOperationSerializer,
    WalletSerializer
)


class WalletSerializerTest(TestCase):
    """Тесты для WalletSerializer"""
    
    def setUp(self):
        """Создаем кошелек для тестов"""
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
    
    def test_wallet_serialization(self):
        """Тест сериализации кошелька"""
        serializer = WalletSerializer(self.wallet)
        data = serializer.data
        
        self.assertEqual(str(data['id']), str(self.wallet.id))
        self.assertEqual(Decimal(str(data['balance'])), self.wallet.balance)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_wallet_serializer_read_only_fields(self):
        """Тест, что поля id, created_at, updated_at только для чтения"""
        serializer = WalletSerializer(self.wallet)
        
        # Пытаемся изменить read-only поля (они должны игнорироваться)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_wallet_serializer_validate_negative_balance(self):
        """Тест валидации отрицательного баланса"""
        serializer = WalletSerializer()
        with self.assertRaises(DRFValidationError):
            serializer.validate_balance(Decimal('-100.00'))
    
    def test_wallet_serializer_validate_positive_balance(self):
        """Тест валидации положительного баланса"""
        serializer = WalletSerializer()
        result = serializer.validate_balance(Decimal('100.00'))
        self.assertEqual(result, Decimal('100.00'))


class WalletOperationSerializerTest(TestCase):
    """Тесты для WalletOperationSerializer"""
    
    def test_valid_deposit_operation(self):
        """Тест валидной операции DEPOSIT"""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['operation_type'], 'DEPOSIT')
        self.assertEqual(serializer.validated_data['amount'], Decimal('100.00'))
    
    def test_valid_withdraw_operation(self):
        """Тест валидной операции WITHDRAW"""
        data = {
            'operation_type': 'WITHDRAW',
            'amount': '50.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['operation_type'], 'WITHDRAW')
        self.assertEqual(serializer.validated_data['amount'], Decimal('50.00'))
    
    def test_invalid_operation_type(self):
        """Тест невалидного типа операции"""
        data = {
            'operation_type': 'INVALID',
            'amount': '100.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('operation_type', serializer.errors)
    
    def test_missing_operation_type(self):
        """Тест отсутствующего типа операции"""
        data = {
            'amount': '100.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('operation_type', serializer.errors)
    
    def test_missing_amount(self):
        """Тест отсутствующей суммы"""
        data = {
            'operation_type': 'DEPOSIT'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_zero_amount(self):
        """Тест нулевой суммы"""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_negative_amount(self):
        """Тест отрицательной суммы"""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '-10.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_minimum_amount(self):
        """Тест минимальной суммы (0.01)"""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.01'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_large_amount(self):
        """Тест большой суммы"""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '999999999999999999.99'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_decimal_precision_valid(self):
        """Тест валидной точности десятичных знаков (2 знака)."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.12'  # Ровно 2 знака после запятой
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Проверяем, что значение корректно обработано
        amount = serializer.validated_data['amount']
        self.assertIsInstance(amount, Decimal)
        self.assertEqual(amount, Decimal('100.12'))

    def test_decimal_precision_invalid(self):
        """Тест невалидной точности десятичных знаков (>2 знаков)."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.123'  # Больше 2 знаков после запятой
        }
        serializer = WalletOperationSerializer(data=data)
        # DecimalField должен отклонить значение с более чем 2 знаками
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

