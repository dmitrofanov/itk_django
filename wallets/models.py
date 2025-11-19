from django.db import models
import uuid


class Wallet(models.Model):
    """
    Модель кошелька с балансом.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        ordering = ['-created_at']

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
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='operations')
    operation_type = models.CharField(max_length=10, choices=OPERATION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_operations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.operation_type} {self.amount} for wallet {self.wallet.id}"


