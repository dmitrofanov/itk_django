from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from wallets.models import Wallet, WalletOperation


class ConcurrentOperationsTest(TransactionTestCase):
    """
    Tests for concurrent operations handling.

    Uses TransactionTestCase instead of TestCase because:
    - TestCase uses transactions that are not visible in other threads
    - TransactionTestCase commits changes to DB, making them available
      for all threads
    """

    def setUp(self):
        """Set up test client and wallet."""
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
        # Store UUID for use in threads
        self.wallet_uuid = str(self.wallet.id)

    def tearDown(self):
        """Close all DB connections after test."""
        # Close all database connections
        # Required for concurrent tests to avoid errors when deleting test DB
        connections.close_all()
    
    def test_concurrent_deposits(self):
        """Test concurrent DEPOSIT operations."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        initial_balance = Decimal('1000.00')
        deposit_amount = Decimal('100.00')
        num_threads = 10

        def make_deposit():
            # Create separate client for each thread
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'DEPOSIT',
                    'amount': str(deposit_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                # Close DB connections in this thread
                connections.close_all()

        # Execute concurrent deposits
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(make_deposit)
                for _ in range(num_threads)
            ]
            results = [future.result() for future in as_completed(futures)]

        # All operations should succeed
        self.assertTrue(all(results))

        # Check final balance
        self.wallet.refresh_from_db()
        expected_balance = initial_balance + (deposit_amount * num_threads)
        self.assertEqual(self.wallet.balance, expected_balance)

        # Check operations count
        operations_count = WalletOperation.objects.filter(
            wallet=self.wallet
        ).count()
        self.assertEqual(operations_count, num_threads)
    
    def test_concurrent_withdraws_with_sufficient_balance(self):
        """Test concurrent WITHDRAW operations with sufficient balance."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        initial_balance = Decimal('1000.00')
        withdraw_amount = Decimal('50.00')
        # 10 * 50 = 500, less than 1000
        num_threads = 10

        def make_withdraw():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'WITHDRAW',
                    'amount': str(withdraw_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()

        # Execute concurrent withdrawals
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(make_withdraw)
                for _ in range(num_threads)
            ]
            results = [future.result() for future in as_completed(futures)]

        # All operations should succeed
        self.assertTrue(all(results))

        # Check final balance
        self.wallet.refresh_from_db()
        expected_balance = initial_balance - (withdraw_amount * num_threads)
        self.assertEqual(self.wallet.balance, expected_balance)
    
    def test_concurrent_mixed_operations(self):
        """Test concurrent mixed operations (DEPOSIT and WITHDRAW)."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        initial_balance = Decimal('1000.00')
        deposit_amount = Decimal('100.00')
        withdraw_amount = Decimal('50.00')
        num_deposits = 10
        num_withdraws = 5

        def make_deposit():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'DEPOSIT',
                    'amount': str(deposit_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()

        def make_withdraw():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'WITHDRAW',
                    'amount': str(withdraw_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()

        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            # Add deposits
            for _ in range(num_deposits):
                futures.append(executor.submit(make_deposit))
            # Add withdrawals
            for _ in range(num_withdraws):
                futures.append(executor.submit(make_withdraw))

            results = [future.result() for future in as_completed(futures)]

        # All operations should succeed
        self.assertTrue(all(results))

        # Check final balance
        self.wallet.refresh_from_db()
        expected_balance = (
            initial_balance +
            (deposit_amount * num_deposits) -
            (withdraw_amount * num_withdraws)
        )
        self.assertEqual(self.wallet.balance, expected_balance)

        # Check operations count
        operations_count = WalletOperation.objects.filter(
            wallet=self.wallet
        ).count()
        self.assertEqual(operations_count, num_deposits + num_withdraws)
    
    def test_concurrent_withdraws_insufficient_balance(self):
        """Test concurrent WITHDRAW operations with insufficient balance."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        initial_balance = Decimal('1000.00')
        withdraw_amount = Decimal('200.00')
        # 10 * 200 = 2000, more than 1000
        num_threads = 10

        def make_withdraw():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'WITHDRAW',
                    'amount': str(withdraw_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()

        # Execute concurrent withdrawals
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(make_withdraw)
                for _ in range(num_threads)
            ]
            results = [future.result() for future in as_completed(futures)]

        # Some operations should succeed, some should fail
        successful = sum(results)
        failed = num_threads - successful

        # Should have at least some successful and some failed
        self.assertGreater(
            successful, 0,
            "At least some withdrawals should succeed"
        )
        self.assertGreater(
            failed, 0,
            "Some withdrawals should fail due to insufficient balance"
        )

        # Check balance is not negative
        self.wallet.refresh_from_db()
        self.assertGreaterEqual(self.wallet.balance, Decimal('0.00'))

        # Check balance is correct (not more than initial)
        self.assertLessEqual(self.wallet.balance, initial_balance)

        # Check successful operations count
        operations_count = WalletOperation.objects.filter(
            wallet=self.wallet
        ).count()
        self.assertEqual(operations_count, successful)
    
    def test_race_condition_prevention(self):
        """Test race condition prevention in simultaneous operations."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        initial_balance = Decimal('1000.00')
        num_operations = 20
        operation_amount = Decimal('10.00')

        def make_operation(operation_type):
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': operation_type,
                    'amount': str(operation_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK, operation_type
            finally:
                connections.close_all()

        # Execute many operations simultaneously
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            # Alternate DEPOSIT and WITHDRAW
            for i in range(num_operations):
                op_type = 'DEPOSIT' if i % 2 == 0 else 'WITHDRAW'
                futures.append(executor.submit(make_operation, op_type))

            results = [future.result() for future in as_completed(futures)]

        # All operations should succeed (balance is sufficient)
        all_successful = all(result[0] for result in results)
        self.assertTrue(all_successful, "All operations should succeed")

        # Check final balance
        self.wallet.refresh_from_db()
        # Calculate expected balance
        deposits = sum(1 for r in results if r[1] == 'DEPOSIT')
        withdraws = sum(1 for r in results if r[1] == 'WITHDRAW')
        expected_balance = (
            initial_balance +
            (operation_amount * deposits) -
            (operation_amount * withdraws)
        )

        self.assertEqual(self.wallet.balance, expected_balance)

        # Check operations count
        operations_count = WalletOperation.objects.filter(
            wallet=self.wallet
        ).count()
        self.assertEqual(operations_count, num_operations)
    


