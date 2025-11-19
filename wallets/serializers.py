from rest_framework import serializers
from .models import Wallet, WalletOperation


class WalletSerializer(serializers.ModelSerializer):
    """
    Сериализатор для кошелька.
    """
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WalletOperationSerializer(serializers.Serializer):
    """
    Сериализатор для операции с кошельком.
    """
    operation_type = serializers.ChoiceField(choices=['DEPOSIT', 'WITHDRAW'])
    amount = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=0.01)


