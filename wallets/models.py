import uuid
from decimal import Decimal

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


class Wallet(models.Model):
    """Wallet model with balance."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
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


