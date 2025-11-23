from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from wallets.models import Wallet, WalletOperation


class WalletModelTest(TestCase):
    """Тесты для модели Wallet"""
    
    def test_wallet_creation(self):
        """Тест создания кошелька с дефолтным балансом"""
        wallet = Wallet.objects.create()
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertIsNotNone(wallet.id)
        self.assertIsNotNone(wallet.created_at)
        self.assertIsNotNone(wallet.updated_at)
    
    def test_wallet_creation_with_balance(self):
        """Тест создания кошелька с указанным балансом"""
        wallet = Wallet.objects.create(balance=Decimal('1000.50'))
        self.assertEqual(wallet.balance, Decimal('1000.50'))
    
    def test_wallet_str_representation(self):
        """Тест строкового представления кошелька"""
        wallet = Wallet.objects.create(balance=Decimal('500.00'))
        str_repr = str(wallet)
        self.assertIn(str(wallet.id), str_repr)
        self.assertIn('500.00', str_repr)
    
    def test_wallet_clean_negative_balance(self):
        """Тест валидации отрицательного баланса"""
        wallet = Wallet(balance=Decimal('-100.00'))
        with self.assertRaises(ValidationError):
            wallet.clean()
    
    def test_wallet_clean_zero_balance(self):
        """Тест валидации нулевого баланса (должен быть валидным)"""
        wallet = Wallet(balance=Decimal('0.00'))
        try:
            wallet.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for zero balance")
    
    def test_wallet_clean_positive_balance(self):
        """Тест валидации положительного баланса"""
        wallet = Wallet(balance=Decimal('100.00'))
        try:
            wallet.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for positive balance")


class WalletOperationModelTest(TestCase):
    """Тесты для модели WalletOperation"""
    
    def setUp(self):
        """Создаем кошелек для тестов"""
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
    
    def test_operation_creation_deposit(self):
        """Тест создания операции DEPOSIT"""
        operation = WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('100.00')
        )
        self.assertEqual(operation.wallet, self.wallet)
        self.assertEqual(operation.operation_type, 'DEPOSIT')
        self.assertEqual(operation.amount, Decimal('100.00'))
        self.assertIsNotNone(operation.id)
        self.assertIsNotNone(operation.created_at)
    
    def test_operation_creation_withdraw(self):
        """Тест создания операции WITHDRAW"""
        operation = WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='WITHDRAW',
            amount=Decimal('200.00')
        )
        self.assertEqual(operation.wallet, self.wallet)
        self.assertEqual(operation.operation_type, 'WITHDRAW')
        self.assertEqual(operation.amount, Decimal('200.00'))
        self.assertIsNotNone(operation.id)
        self.assertIsNotNone(operation.created_at)
    
    def test_operation_str_representation(self):
        """Тест строкового представления операции"""
        operation = WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('150.00')
        )
        str_repr = str(operation)
        self.assertIn('DEPOSIT', str_repr)
        self.assertIn('150.00', str_repr)
        self.assertIn(str(self.wallet.id), str_repr)
    
    def test_operation_clean_zero_amount(self):
        """Тест валидации нулевой суммы операции"""
        operation = WalletOperation(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('0.00')
        )
        with self.assertRaises(ValidationError):
            operation.clean()
    
    def test_operation_clean_negative_amount(self):
        """Тест валидации отрицательной суммы операции"""
        operation = WalletOperation(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError):
            operation.clean()
    
    def test_operation_clean_positive_amount(self):
        """Тест валидации положительной суммы операции"""
        operation = WalletOperation(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('50.00')
        )
        try:
            operation.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for positive amount")
    
    def test_operation_related_name(self):
        """Тест связи operations через related_name"""
        WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('100.00')
        )
        WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='WITHDRAW',
            amount=Decimal('50.00')
        )
        
        operations = self.wallet.operations.all()
        self.assertEqual(operations.count(), 2)
    
    def test_operation_cascade_delete(self):
        """Тест каскадного удаления операций при удалении кошелька"""
        WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('100.00')
        )
        
        wallet_id = self.wallet.id
        self.wallet.delete()
        
        # Проверяем, что операция тоже удалена
        self.assertFalse(WalletOperation.objects.filter(wallet_id=wallet_id).exists())

