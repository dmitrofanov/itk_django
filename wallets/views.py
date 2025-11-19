from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Wallet, WalletOperation
from .serializers import WalletSerializer, WalletOperationSerializer


@api_view(['GET'])
def wallet_detail(request, wallet_uuid):
    """
    Получить информацию о кошельке по UUID.
    GET /api/v1/wallets/{WALLET_UUID}
    """
    wallet = get_object_or_404(Wallet, id=wallet_uuid)
    serializer = WalletSerializer(wallet)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def wallet_operation(request, wallet_uuid):
    """
    Выполнить операцию с кошельком (DEPOSIT или WITHDRAW).
    POST /api/v1/wallets/{WALLET_UUID}/operation
    
    Body:
    {
        "operation_type": "DEPOSIT" or "WITHDRAW",
        "amount": 1000
    }
    """
    wallet = get_object_or_404(Wallet, id=wallet_uuid)
    
    serializer = WalletOperationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    operation_type = serializer.validated_data['operation_type']
    amount = serializer.validated_data['amount']
    
    # Используем select_for_update для блокировки строки и предотвращения race conditions
    with transaction.atomic():
        # Блокируем кошелек для обновления
        wallet = Wallet.objects.select_for_update().get(id=wallet_uuid)
        
        if operation_type == 'DEPOSIT':
            wallet.balance += amount
        elif operation_type == 'WITHDRAW':
            if wallet.balance < amount:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            wallet.balance -= amount
        
        wallet.save()
        
        # Сохраняем операцию в историю
        WalletOperation.objects.create(
            wallet=wallet,
            operation_type=operation_type,
            amount=amount
        )
    
    serializer_wallet = WalletSerializer(wallet)
    return Response(serializer_wallet.data, status=status.HTTP_200_OK)

