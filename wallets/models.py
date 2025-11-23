import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    """Wallet model with balance."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        # Order by creation date, newest first
        ordering = ['-created_at']

    def clean(self):
        """Validate model-level constraints."""
        if self.balance < 0:
            raise ValidationError({
                'balance': 'Balance cannot be negative'
            })

    def __str__(self):
        return f"Wallet {self.id} - Balance: {self.balance}"


class WalletOperation(models.Model):
    """Model for storing wallet operation history."""
    # Available operation types
    OPERATION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
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
        max_length=10,
        choices=OPERATION_TYPES
    )
    # Minimum operation amount
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_operations'
        # Order by creation date, newest first
        ordering = ['-created_at']

    def clean(self):
        """Validate model-level constraints."""
        if self.amount <= 0:
            raise ValidationError({
                'amount': 'Amount must be greater than zero'
            })

    def __str__(self):
        return f"{self.operation_type} {self.amount} for wallet {self.wallet.id}"


