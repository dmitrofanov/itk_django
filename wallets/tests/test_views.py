import uuid
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from wallets.models import Wallet, WalletOperation


class WalletDetailViewTest(TestCase):
    """Tests for GET /api/v1/wallets/{uuid}."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))

    def test_get_existing_wallet(self):
        """Test getting existing wallet."""
        url = reverse('wallets:wallet-detail', kwargs={'wallet_uuid': self.wallet.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['balance'])), self.wallet.balance)
        self.assertEqual(str(response.data['id']), str(self.wallet.id))
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
    
    def test_get_nonexistent_wallet(self):
        """Test getting non-existent wallet."""
        fake_uuid = uuid.uuid4()
        url = reverse(
            'wallets:wallet-detail',
            kwargs={'wallet_uuid': fake_uuid}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wallet_invalid_uuid_format(self):
        """Test getting wallet with invalid UUID format."""
        url = '/api/v1/wallets/invalid-uuid/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wallet_method_not_allowed(self):
        """Test that POST is not allowed for this endpoint."""
        url = reverse('wallets:wallet-detail', kwargs={'wallet_uuid': self.wallet.id})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class WalletOperationViewTest(TestCase):
    """Tests for POST /api/v1/wallets/{uuid}/operation."""

    def setUp(self):
        """Set up test client and wallet."""
        self.client = APIClient()
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))

    def test_deposit_operation_success(self):
        """Test successful DEPOSIT operation."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '500.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1500.00'))

        # Check operation is saved to history
        operation = WalletOperation.objects.filter(
            wallet=self.wallet
        ).first()
        self.assertIsNotNone(operation)
        self.assertEqual(operation.operation_type, 'DEPOSIT')
        self.assertEqual(operation.amount, Decimal('500.00'))

    def test_withdraw_operation_success(self):
        """Test successful WITHDRAW operation."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'WITHDRAW',
            'amount': '300.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('700.00'))

        # Check operation in history
        operation = WalletOperation.objects.filter(
            wallet=self.wallet
        ).first()
        self.assertEqual(operation.operation_type, 'WITHDRAW')
        self.assertEqual(operation.amount, Decimal('300.00'))

    def test_withdraw_insufficient_balance(self):
        """Test withdrawal with insufficient balance."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'WITHDRAW',
            'amount': '2000.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Insufficient balance')

        # Check balance didn't change
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))

        # Check operation was not created
        self.assertFalse(
            WalletOperation.objects.filter(wallet=self.wallet).exists()
        )

    def test_operation_nonexistent_wallet(self):
        """Test operation with non-existent wallet."""
        fake_uuid = uuid.uuid4()
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': fake_uuid})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Wallet not found')
    
    def test_operation_invalid_operation_type(self):
        """Test operation with invalid type."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'INVALID',
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('operation_type', response.data)

    def test_operation_missing_operation_type(self):
        """Test operation without type."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('operation_type', response.data)

    def test_operation_missing_amount(self):
        """Test operation without amount."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'DEPOSIT'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_operation_zero_amount(self):
        """Test operation with zero amount."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_operation_negative_amount(self):
        """Test operation with negative amount."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '-10.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_operation_minimum_amount(self):
        """Test operation with minimum amount (0.01)."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.01'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.01'))

    def test_multiple_operations_sequence(self):
        """Test sequence of operations."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )

        # DEPOSIT 500
        response1 = self.client.post(url, {
            'operation_type': 'DEPOSIT',
            'amount': '500.00'
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # WITHDRAW 200
        response2 = self.client.post(url, {
            'operation_type': 'WITHDRAW',
            'amount': '200.00'
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # DEPOSIT 100
        response3 = self.client.post(url, {
            'operation_type': 'DEPOSIT',
            'amount': '100.00'
        }, format='json')
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        # Check final balance
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1400.00'))

        # Check operations count in history
        operations_count = WalletOperation.objects.filter(
            wallet=self.wallet
        ).count()
        self.assertEqual(operations_count, 3)

    def test_operation_response_structure(self):
        """Test operation response structure."""
        url = reverse(
            'wallets:wallet-operation',
            kwargs={'wallet_uuid': self.wallet.id}
        )
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '250.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertIn('balance', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        self.assertEqual(
            Decimal(str(response.data['balance'])),
            Decimal('1250.00')
        )

    def test_operation_method_not_allowed(self):
        """Test that GET is not allowed for this endpoint."""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

