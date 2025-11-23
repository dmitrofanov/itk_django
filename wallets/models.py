import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    """
    Модель кошелька с балансом.
    """
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
        ordering = ['-created_at']

    def clean(self):
        """Валидация на уровне модели."""
        if self.balance < 0:
            raise ValidationError({
                'balance': 'Balance cannot be negative'
            })

    def __str__(self):
        return f"Wallet {self.id} - Balance: {self.balance}"


class WalletOperation(models.Model):
    """
    Модель для хранения истории операций с кошельком.
    """
    OPERATION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Индекс для быстрого поиска операций по кошельку
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
    # Минимальная сумма операции
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_operations'
        ordering = ['-created_at']

    def clean(self):
        """Валидация на уровне модели."""
        if self.amount <= 0:
            raise ValidationError({
                'amount': 'Amount must be greater than zero'
            })

    def __str__(self):
        return f"{self.operation_type} {self.amount} for wallet {self.wallet.id}"


