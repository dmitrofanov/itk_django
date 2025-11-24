import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (
    DECIMAL_MAX_DIGITS,
    DECIMAL_PLACES,
    OPERATION_MIN_AMOUNT,
    OPERATION_TYPE_DEPOSIT,
    OPERATION_TYPE_MAX_LENGTH,
    OPERATION_TYPE_WITHDRAW,
    WALLET_DEFAULT_BALANCE,
    WALLET_MIN_BALANCE,
)
from .exceptions import InsufficientBalanceError

# Logger for wallet operations
logger = logging.getLogger('wallets')


class Wallet(models.Model):
    """Wallet model with balance."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets',
        db_index=True,
    )
    balance = models.DecimalField(
        max_digits=DECIMAL_MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        default=WALLET_DEFAULT_BALANCE,
        validators=[MinValueValidator(WALLET_MIN_BALANCE)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        # Order by creation date, newest first
        ordering = ['-created_at']

    def clean(self):
        """Validate model-level constraints."""
        if self.balance < WALLET_MIN_BALANCE:
            raise ValidationError({
                'balance': 'Balance cannot be negative'
            })

    def deposit(self, amount):
        """
        Deposit amount to wallet balance.

        Args:
            amount: Amount to deposit
            operation_type: Type of operation (default: OPERATION_TYPE_DEPOSIT)

        Returns:
            None
        """
        old_balance = self.balance
        self.balance += amount
        logger.info(
            'Deposit operation completed',
            extra={
                'wallet_uuid': str(self.id),
                'operation_type': OPERATION_TYPE_DEPOSIT,
                'amount': str(amount),
                'old_balance': str(old_balance),
                'new_balance': str(self.balance),
            }
        )

    def withdraw(self, amount):
        """
        Withdraw amount from wallet balance.

        Args:
            amount: Amount to withdraw
            operation_type: Type of operation (default: OPERATION_TYPE_WITHDRAW)

        Raises:
            InsufficientBalanceError: If insufficient balance for withdrawal

        Returns:
            None
        """
        if self.balance < amount:
            logger.warning(
                'Insufficient balance for withdrawal',
                extra={
                    'wallet_uuid': str(self.id),
                    'operation_type': OPERATION_TYPE_WITHDRAW,
                    'amount': str(amount),
                    'current_balance': str(self.balance),
                    'error_type': 'InsufficientBalanceError',
                }
            )
            raise InsufficientBalanceError(
                f"Insufficient balance. "
                f"Current balance: {self.balance}, Required: {amount}"
            )
        old_balance = self.balance
        self.balance -= amount
        logger.info(
            'Withdraw operation completed',
            extra={
                'wallet_uuid': str(self.id),
                'operation_type': OPERATION_TYPE_WITHDRAW,
                'amount': str(amount),
                'old_balance': str(old_balance),
                'new_balance': str(self.balance),
            }
        )

    def __str__(self):
        return f"Wallet {self.id} - Balance: {self.balance}"


class WalletOperation(models.Model):
    """Model for storing wallet operation history."""
    # Available operation types
    OPERATION_TYPES = [
        (OPERATION_TYPE_DEPOSIT, 'Deposit'),
        (OPERATION_TYPE_WITHDRAW, 'Withdraw'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # Index for fast wallet operations lookup
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='operations',
        db_index=True
    )
    operation_type = models.CharField(
        max_length=OPERATION_TYPE_MAX_LENGTH,
        choices=OPERATION_TYPES
    )
    # Minimum operation amount
    amount = models.DecimalField(
        max_digits=DECIMAL_MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        validators=[MinValueValidator(OPERATION_MIN_AMOUNT)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_operations'
        # Order by creation date, newest first
        ordering = ['-created_at']

    def clean(self):
        """Validate model-level constraints."""
        if self.amount < OPERATION_MIN_AMOUNT:
            raise ValidationError({
                'amount': 'Amount must be greater than zero'
            })

    def __str__(self):
        return f"{self.operation_type} {self.amount} for wallet {self.wallet.id}"


