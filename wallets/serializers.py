from decimal import Decimal

from rest_framework import serializers

from .constants import (
    DECIMAL_MAX_DIGITS,
    DECIMAL_PLACES,
    OPERATION_MIN_AMOUNT,
    WALLET_MIN_BALANCE,
)
from .models import Wallet, WalletOperation


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet."""

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at', 'updated_at']
        # Prevent modification of system fields
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_balance(self, value):
        """Validate balance (if used for update)."""
        if value < WALLET_MIN_BALANCE:
            raise serializers.ValidationError(
                "Balance cannot be negative"
            )
        return value


class WalletOperationSerializer(serializers.Serializer):
    """Serializer for wallet operation."""

    # Use constants from model
    operation_type = serializers.ChoiceField(
        choices=[
            choice[0]
            for choice in WalletOperation.OPERATION_TYPES
        ]
    )
    amount = serializers.DecimalField(
        max_digits=DECIMAL_MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
        min_value=OPERATION_MIN_AMOUNT
    )


