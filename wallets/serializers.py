from decimal import Decimal

from rest_framework import serializers

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
        if value < 0:
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
        max_digits=20,
        decimal_places=2,
        min_value=Decimal('0.01')
    )

    def validate_amount(self, value):
        """Additional amount validation."""
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero"
            )
        return value


