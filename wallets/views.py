import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Wallet, WalletOperation
from .serializers import WalletSerializer, WalletOperationSerializer

logger = logging.getLogger('wallets')


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
    serializer = WalletOperationSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid operation data for wallet {wallet_uuid}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    operation_type = serializer.validated_data['operation_type']
    amount = serializer.validated_data['amount']
    
    try:
        # Используем select_for_update для блокировки строки и предотвращения race conditions
        with transaction.atomic():
            # Проверяем существование кошелька и блокируем для обновления
            try:
                wallet = Wallet.objects.select_for_update().get(id=wallet_uuid)
            except Wallet.DoesNotExist:
                logger.warning(f"Wallet {wallet_uuid} not found")
                return Response(
                    {'error': 'Wallet not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Выполняем операцию
            if operation_type == 'DEPOSIT':
                wallet.balance += amount
                logger.info(f"Deposit {amount} to wallet {wallet_uuid}. New balance: {wallet.balance}")
            elif operation_type == 'WITHDRAW':
                if wallet.balance < amount:
                    logger.warning(f"Insufficient balance for wallet {wallet_uuid}. Balance: {wallet.balance}, Requested: {amount}")
                    return Response(
                        {'error': 'Insufficient balance'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                wallet.balance -= amount
                logger.info(f"Withdraw {amount} from wallet {wallet_uuid}. New balance: {wallet.balance}")
            
            wallet.save()
            
            # Сохраняем операцию в историю
            WalletOperation.objects.create(
                wallet=wallet,
                operation_type=operation_type,
                amount=amount
            )
        
        serializer_wallet = WalletSerializer(wallet)
        return Response(serializer_wallet.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error processing operation for wallet {wallet_uuid}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

