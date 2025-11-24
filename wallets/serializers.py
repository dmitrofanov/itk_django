from decimal import Decimal

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from rest_framework import serializers

from .constants import (
    DECIMAL_MAX_DIGITS,
    DECIMAL_PLACES,
    OPERATION_MIN_AMOUNT,
    WALLET_MIN_BALANCE,
)
from .models import Wallet, WalletOperation


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='Wallet example response',
            value={
                'id': '123e4567-e89b-12d3-a456-426614174000',
                'balance': '1000.00',
                'created_at': '2025-01-19T10:00:00Z',
                'updated_at': '2025-01-19T10:30:00Z',
            },
        ),
    ]
)
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


