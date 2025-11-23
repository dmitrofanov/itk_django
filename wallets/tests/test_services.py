import uuid
from decimal import Decimal

from django.test import TestCase

from wallets.exceptions import (
    InsufficientBalanceError,
    UnknownOperationTypeError,
    WalletNotFoundError,
)
from wallets.models import Wallet, WalletOperation
from wallets.services import execute_wallet_operation


class WalletServiceTest(TestCase):
    """Tests for execute_wallet_operation function."""

    def setUp(self):
        """Set up test wallet."""
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
        self.wallet_uuid = self.wallet.id

    def test_deposit_operation_success(self):
        """Test successful DEPOSIT operation."""
        initial_balance = self.wallet.balance
        deposit_amount = Decimal('500.00')
        expected_balance = initial_balance + deposit_amount

        # Execute deposit
        updated_wallet = execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )

        # Refresh from database
        self.wallet.refresh_from_db()

        # Check balance updated correctly
        self.assertEqual(self.wallet.balance, expected_balance)
        self.assertEqual(updated_wallet.balance, expected_balance)
        self.assertEqual(updated_wallet.id, self.wallet.id)

        # Check operation saved to history
        operation = WalletOperation.objects.filter(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=deposit_amount
        ).first()
        self.assertIsNotNone(operation)
        self.assertEqual(operation.wallet.id, self.wallet.id)

    def test_withdraw_operation_success(self):
        """Test successful WITHDRAW operation."""
        initial_balance = self.wallet.balance
        withdraw_amount = Decimal('300.00')
        expected_balance = initial_balance - withdraw_amount

        # Execute withdraw
        updated_wallet = execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='WITHDRAW',
            amount=withdraw_amount
        )

        # Refresh from database
        self.wallet.refresh_from_db()

        # Check balance updated correctly
        self.assertEqual(self.wallet.balance, expected_balance)
        self.assertEqual(updated_wallet.balance, expected_balance)

        # Check operation saved to history
        operation = WalletOperation.objects.filter(
            wallet=self.wallet,
            operation_type='WITHDRAW',
            amount=withdraw_amount
        ).first()
        self.assertIsNotNone(operation)

    def test_withdraw_insufficient_balance(self):
        """Test WITHDRAW operation with insufficient balance."""
        withdraw_amount = Decimal('2000.00')  # More than balance

        # Should raise InsufficientBalanceError
        with self.assertRaises(InsufficientBalanceError) as context:
            execute_wallet_operation(
                wallet_uuid=self.wallet_uuid,
                operation_type='WITHDRAW',
                amount=withdraw_amount
            )

        # Check error message
        self.assertIn('Insufficient balance', str(context.exception))

        # Check balance unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))

        # Check no operation saved
        operation = WalletOperation.objects.filter(
            wallet=self.wallet,
            operation_type='WITHDRAW',
            amount=withdraw_amount
        ).first()
        self.assertIsNone(operation)

    def test_withdraw_exact_balance(self):
        """Test WITHDRAW operation with exact balance."""
        withdraw_amount = self.wallet.balance
        expected_balance = Decimal('0.00')

        # Execute withdraw
        execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='WITHDRAW',
            amount=withdraw_amount
        )

        # Check balance is zero
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, expected_balance)

    def test_wallet_not_found(self):
        """Test operation with non-existent wallet."""
        fake_uuid = uuid.uuid4()
        deposit_amount = Decimal('100.00')

        # Should raise WalletNotFoundError
        with self.assertRaises(WalletNotFoundError):
            execute_wallet_operation(
                wallet_uuid=fake_uuid,
                operation_type='DEPOSIT',
                amount=deposit_amount
            )

    def test_unknown_operation_type(self):
        """Test operation with unknown operation type."""
        deposit_amount = Decimal('100.00')

        # Should raise UnknownOperationTypeError
        with self.assertRaises(UnknownOperationTypeError) as context:
            execute_wallet_operation(
                wallet_uuid=self.wallet_uuid,
                operation_type='UNKNOWN',
                amount=deposit_amount
            )

        # Check error message
        self.assertIn('Unknown operation type', str(context.exception))

        # Check balance unchanged
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))

        # Check no operation saved
        operation = WalletOperation.objects.filter(
            wallet=self.wallet
        ).first()
        self.assertIsNone(operation)

    def test_multiple_deposits_sequence(self):
        """Test sequence of multiple DEPOSIT operations."""
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('50.00')]
        expected_balance = self.wallet.balance + sum(amounts)

        # Execute multiple deposits
        for amount in amounts:
            execute_wallet_operation(
                wallet_uuid=self.wallet_uuid,
                operation_type='DEPOSIT',
                amount=amount
            )

        # Check final balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, expected_balance)

        # Check all operations saved
        operations = WalletOperation.objects.filter(
            wallet=self.wallet,
            operation_type='DEPOSIT'
        )
        self.assertEqual(operations.count(), len(amounts))

    def test_multiple_withdraws_sequence(self):
        """Test sequence of multiple WITHDRAW operations."""
        amounts = [Decimal('100.00'), Decimal('200.00'), Decimal('50.00')]
        expected_balance = self.wallet.balance - sum(amounts)

        # Execute multiple withdraws
        for amount in amounts:
            execute_wallet_operation(
                wallet_uuid=self.wallet_uuid,
                operation_type='WITHDRAW',
                amount=amount
            )

        # Check final balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, expected_balance)

    def test_mixed_operations_sequence(self):
        """Test sequence of mixed DEPOSIT and WITHDRAW operations."""
        operations = [
            ('DEPOSIT', Decimal('500.00')),
            ('WITHDRAW', Decimal('200.00')),
            ('DEPOSIT', Decimal('100.00')),
            ('WITHDRAW', Decimal('50.00')),
        ]
        expected_balance = self.wallet.balance
        for op_type, amount in operations:
            if op_type == 'DEPOSIT':
                expected_balance += amount
            else:
                expected_balance -= amount

        # Execute operations
        for op_type, amount in operations:
            execute_wallet_operation(
                wallet_uuid=self.wallet_uuid,
                operation_type=op_type,
                amount=amount
            )

        # Check final balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, expected_balance)

        # Check all operations saved
        operations_count = WalletOperation.objects.filter(
            wallet=self.wallet
        ).count()
        self.assertEqual(operations_count, len(operations))

    def test_deposit_zero_balance_wallet(self):
        """Test DEPOSIT operation on wallet with zero balance."""
        # Create wallet with zero balance
        zero_wallet = Wallet.objects.create(balance=Decimal('0.00'))
        deposit_amount = Decimal('100.00')

        # Execute deposit
        execute_wallet_operation(
            wallet_uuid=zero_wallet.id,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )

        # Check balance updated
        zero_wallet.refresh_from_db()
        self.assertEqual(zero_wallet.balance, deposit_amount)

    def test_deposit_small_amount(self):
        """Test DEPOSIT operation with small amount (0.01)."""
        deposit_amount = Decimal('0.01')
        initial_balance = self.wallet.balance

        # Execute deposit
        execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )

        # Check balance updated
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance + deposit_amount
        )

    def test_deposit_large_amount(self):
        """Test DEPOSIT operation with large amount."""
        deposit_amount = Decimal('99999999999999999.99')
        initial_balance = self.wallet.balance

        # Execute deposit
        execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )

        # Check balance updated
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance + deposit_amount
        )

    def test_withdraw_after_deposit(self):
        """Test WITHDRAW operation after DEPOSIT in same wallet."""
        deposit_amount = Decimal('500.00')
        withdraw_amount = Decimal('300.00')
        expected_balance = (
            self.wallet.balance + deposit_amount - withdraw_amount
        )

        # Execute deposit
        execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )

        # Execute withdraw
        execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='WITHDRAW',
            amount=withdraw_amount
        )

        # Check final balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, expected_balance)

    def test_operation_creates_audit_trail(self):
        """Test that operation creates proper audit trail."""
        deposit_amount = Decimal('250.00')

        # Execute operation
        execute_wallet_operation(
            wallet_uuid=self.wallet_uuid,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )

        # Check operation record
        operation = WalletOperation.objects.get(
            wallet=self.wallet,
            operation_type='DEPOSIT',
            amount=deposit_amount
        )
        self.assertIsNotNone(operation.id)
        self.assertIsNotNone(operation.created_at)
        self.assertEqual(operation.wallet.id, self.wallet.id)

    def test_transaction_rollback_on_error(self):
        """Test that transaction rolls back on error."""
        initial_balance = self.wallet.balance
        withdraw_amount = Decimal('2000.00')  # More than balance

        # Attempt withdraw that will fail
        with self.assertRaises(InsufficientBalanceError):
            execute_wallet_operation(
                wallet_uuid=self.wallet_uuid,
                operation_type='WITHDRAW',
                amount=withdraw_amount
            )

        # Check balance unchanged (transaction rolled back)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, initial_balance)

        # Check no operation saved
        operation = WalletOperation.objects.filter(
            wallet=self.wallet,
            amount=withdraw_amount
        ).first()
        self.assertIsNone(operation)

