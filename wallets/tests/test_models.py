from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from wallets.exceptions import InsufficientBalanceError
from wallets.models import Wallet, WalletOperation


User = get_user_model()


class WalletModelTest(TestCase):
    """Tests for Wallet model."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='wallet_model_user',
            email='wallet_model@example.com',
            password='testpass123'
        )

    def test_wallet_creation(self):
        """Test wallet creation with default balance."""
        wallet = Wallet.objects.create(user=self.user)
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertIsNotNone(wallet.id)
        self.assertIsNotNone(wallet.created_at)
        self.assertIsNotNone(wallet.updated_at)

    def test_wallet_creation_with_balance(self):
        """Test wallet creation with specified balance."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.50')
        )
        self.assertEqual(wallet.balance, Decimal('1000.50'))

    def test_wallet_str_representation(self):
        """Test wallet string representation."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('500.00')
        )
        str_repr = str(wallet)
        self.assertIn(str(wallet.id), str_repr)
        self.assertIn('500.00', str_repr)

    def test_wallet_clean_negative_balance(self):
        """Test negative balance validation."""
        wallet = Wallet(balance=Decimal('-100.00'))
        with self.assertRaises(ValidationError):
            wallet.clean()

    def test_wallet_clean_zero_balance(self):
        """Test zero balance validation (should be valid)."""
        wallet = Wallet(balance=Decimal('0.00'))
        try:
            wallet.clean()
        except ValidationError:
            self.fail(
                "clean() raised ValidationError unexpectedly for zero balance"
            )

    def test_wallet_clean_positive_balance(self):
        """Test positive balance validation."""
        wallet = Wallet(balance=Decimal('100.00'))
        try:
            wallet.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for positive balance")

    def test_deposit_positive_amount(self):
        """Test deposit with positive amount."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        old_balance = wallet.balance
        deposit_amount = Decimal('50.00')
        
        wallet.deposit(deposit_amount)
        
        self.assertEqual(wallet.balance, old_balance + deposit_amount)
        self.assertEqual(wallet.balance, Decimal('150.00'))

    def test_deposit_zero_balance(self):
        """Test deposit on wallet with zero balance."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('0.00')
        )
        deposit_amount = Decimal('100.00')
        
        wallet.deposit(deposit_amount)
        
        self.assertEqual(wallet.balance, deposit_amount)

    def test_deposit_multiple_times(self):
        """Test multiple deposits."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        
        wallet.deposit(Decimal('50.00'))
        self.assertEqual(wallet.balance, Decimal('150.00'))
        
        wallet.deposit(Decimal('25.50'))
        self.assertEqual(wallet.balance, Decimal('175.50'))
        
        wallet.deposit(Decimal('10.00'))
        self.assertEqual(wallet.balance, Decimal('185.50'))

    def test_withdraw_sufficient_balance(self):
        """Test withdraw with sufficient balance."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )
        old_balance = wallet.balance
        withdraw_amount = Decimal('300.00')
        
        wallet.withdraw(withdraw_amount)
        
        self.assertEqual(wallet.balance, old_balance - withdraw_amount)
        self.assertEqual(wallet.balance, Decimal('700.00'))

    def test_withdraw_exact_balance(self):
        """Test withdraw exact balance amount."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('500.00')
        )
        withdraw_amount = Decimal('500.00')
        
        wallet.withdraw(withdraw_amount)
        
        self.assertEqual(wallet.balance, Decimal('0.00'))

    def test_withdraw_insufficient_balance(self):
        """Test withdraw with insufficient balance raises error."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        withdraw_amount = Decimal('200.00')
        
        with self.assertRaises(InsufficientBalanceError) as context:
            wallet.withdraw(withdraw_amount)
        
        # Check that balance was not changed
        self.assertEqual(wallet.balance, Decimal('100.00'))
        
        # Check error message contains relevant information
        error_message = str(context.exception)
        self.assertIn('Insufficient balance', error_message)
        self.assertIn('100.00', error_message)
        self.assertIn('200.00', error_message)

    def test_withdraw_zero_balance(self):
        """Test withdraw from wallet with zero balance raises error."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('0.00')
        )
        withdraw_amount = Decimal('10.00')
        
        with self.assertRaises(InsufficientBalanceError):
            wallet.withdraw(withdraw_amount)
        
        # Check that balance remains zero
        self.assertEqual(wallet.balance, Decimal('0.00'))

    def test_deposit_and_withdraw_sequence(self):
        """Test sequence of deposit and withdraw operations."""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )
        
        # Initial deposit
        wallet.deposit(Decimal('500.00'))
        self.assertEqual(wallet.balance, Decimal('1500.00'))
        
        # Withdraw
        wallet.withdraw(Decimal('200.00'))
        self.assertEqual(wallet.balance, Decimal('1300.00'))
        
        # Another deposit
        wallet.deposit(Decimal('100.00'))
        self.assertEqual(wallet.balance, Decimal('1400.00'))
        
        # Another withdraw
        wallet.withdraw(Decimal('400.00'))
        self.assertEqual(wallet.balance, Decimal('1000.00'))


class WalletOperationModelTest(TestCase):
    """Tests for WalletOperation model."""

    def setUp(self):
        """Set up wallet for tests."""
        self.user = User.objects.create_user(
            username='wallet_operation_user',
            email='wallet_operation@example.com',
            password='testpass123'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )

    def test_operation_creation_deposit(self):
        """Test DEPOSIT operation creation."""
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
        """Test WITHDRAW operation creation."""
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
        """Test operation string representation."""
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
        """Test zero amount validation."""
        operation = WalletOperation(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('0.00')
        )
        with self.assertRaises(ValidationError):
            operation.clean()

    def test_operation_clean_negative_amount(self):
        """Test negative amount validation."""
        operation = WalletOperation(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError):
            operation.clean()

    def test_operation_clean_positive_amount(self):
        """Test positive amount validation."""
        operation = WalletOperation(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('50.00')
        )
        try:
            operation.clean()
        except ValidationError:
            self.fail(
                "clean() raised ValidationError unexpectedly "
                "for positive amount"
            )

    def test_operation_related_name(self):
        """Test operations relationship via related_name."""
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
        """Test cascade deletion of operations when wallet is deleted."""
        WalletOperation.objects.create(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=Decimal('100.00')
        )

        wallet_id = self.wallet.id
        self.wallet.delete()

        # Check operation is also deleted
        self.assertFalse(
            WalletOperation.objects.filter(wallet_id=wallet_id).exists()
        )

