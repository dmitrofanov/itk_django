from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from wallets.models import Wallet
from wallets.serializers import (
    WalletOperationSerializer,
    WalletSerializer
)


User = get_user_model()


class WalletSerializerTest(TestCase):
    """Tests for WalletSerializer."""

    def setUp(self):
        """Set up wallet for tests."""
        self.user = User.objects.create_user(
            username='wallet_serializer_user',
            email='wallet_serializer@example.com',
            password='testpass123'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00')
        )

    def test_wallet_serialization(self):
        """Test wallet serialization."""
        serializer = WalletSerializer(self.wallet)
        data = serializer.data
        
        self.assertEqual(str(data['id']), str(self.wallet.id))
        self.assertEqual(Decimal(str(data['balance'])), self.wallet.balance)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_wallet_serializer_read_only_fields(self):
        """Test that id, created_at, updated_at fields are read-only."""
        original_id = self.wallet.id
        original_created_at = self.wallet.created_at
        
        # Attempt to update with read-only fields
        # These fields should be ignored during update
        update_data = {
            'id': '00000000-0000-0000-0000-000000000000',  # Try to change ID
            'balance': Decimal('2000.00'),
            'created_at': '2020-01-01T00:00:00Z',  # Try to change created_at
            'updated_at': '2020-01-01T00:00:00Z'   # Try to change updated_at
        }
        
        serializer = WalletSerializer(
            self.wallet,
            data=update_data,
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        # Refresh from database
        self.wallet.refresh_from_db()
        
        # Read-only fields should remain unchanged
        self.assertEqual(self.wallet.id, original_id)
        self.assertEqual(self.wallet.created_at, original_created_at)
        # updated_at will change automatically (auto_now=True), 
        # but not to the value we provided
        self.assertNotEqual(
            str(self.wallet.updated_at),
            '2020-01-01T00:00:00Z'
        )
        # Balance should be updated (not read-only)
        self.assertEqual(self.wallet.balance, Decimal('2000.00'))
    
    def test_wallet_serializer_validate_negative_balance(self):
        """Test negative balance validation."""
        serializer = WalletSerializer()
        with self.assertRaises(DRFValidationError):
            serializer.validate_balance(Decimal('-100.00'))

    def test_wallet_serializer_validate_positive_balance(self):
        """Test positive balance validation."""
        serializer = WalletSerializer()
        result = serializer.validate_balance(Decimal('100.00'))
        self.assertEqual(result, Decimal('100.00'))


class WalletOperationSerializerTest(TestCase):
    """Tests for WalletOperationSerializer."""

    def test_valid_deposit_operation(self):
        """Test valid DEPOSIT operation."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['operation_type'], 'DEPOSIT')
        self.assertEqual(serializer.validated_data['amount'], Decimal('100.00'))
    
    def test_valid_withdraw_operation(self):
        """Test valid WITHDRAW operation."""
        data = {
            'operation_type': 'WITHDRAW',
            'amount': '50.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['operation_type'], 'WITHDRAW')
        self.assertEqual(serializer.validated_data['amount'], Decimal('50.00'))
    
    def test_invalid_operation_type(self):
        """Test invalid operation type."""
        data = {
            'operation_type': 'INVALID',
            'amount': '100.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('operation_type', serializer.errors)
    
    def test_missing_operation_type(self):
        """Test missing operation type."""
        data = {
            'amount': '100.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('operation_type', serializer.errors)
    
    def test_missing_amount(self):
        """Test missing amount."""
        data = {
            'operation_type': 'DEPOSIT'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_zero_amount(self):
        """Test zero amount."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_negative_amount(self):
        """Test negative amount."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '-10.00'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_minimum_amount(self):
        """Test minimum amount (0.01)."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.01'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_large_amount(self):
        """Test large amount."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '999999999999999999.99'
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_decimal_precision_valid(self):
        """Test valid decimal precision (2 decimal places)."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.12'  # Exactly 2 decimal places
        }
        serializer = WalletOperationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Check value is correctly processed
        amount = serializer.validated_data['amount']
        self.assertIsInstance(amount, Decimal)
        self.assertEqual(amount, Decimal('100.12'))

    def test_decimal_precision_invalid(self):
        """Test invalid decimal precision (>2 decimal places)."""
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.123'  # More than 2 decimal places
        }
        serializer = WalletOperationSerializer(data=data)
        # DecimalField should reject values with more than 2 decimal places
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

