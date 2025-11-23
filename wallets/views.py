import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Wallet, WalletOperation
from .serializers import (
    WalletOperationSerializer,
    WalletSerializer
)

# Logger for wallet operations
logger = logging.getLogger('wallets')


@api_view(['GET'])
def wallet_detail(request, wallet_uuid):
    """
    Get wallet information by UUID.

    GET /api/v1/wallets/{WALLET_UUID}
    """
    wallet = get_object_or_404(Wallet, id=wallet_uuid)
    serializer = WalletSerializer(wallet)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def wallet_operation(request, wallet_uuid):
    """
    Execute wallet operation (DEPOSIT or WITHDRAW).

    POST /api/v1/wallets/{WALLET_UUID}/operation

    Body:
    {
        "operation_type": "DEPOSIT" or "WITHDRAW",
        "amount": 1000
    }
    """
    # Validate input data
    serializer = WalletOperationSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            f"Invalid operation data for wallet {wallet_uuid}: "
            f"{serializer.errors}"
        )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    operation_type = serializer.validated_data['operation_type']
    amount = serializer.validated_data['amount']

    try:
        # Use select_for_update to lock row and prevent race conditions
        with transaction.atomic():
            # Check wallet existence and lock for update
            try:
                wallet = Wallet.objects.select_for_update().get(
                    id=wallet_uuid
                )
            except Wallet.DoesNotExist:
                logger.warning(f"Wallet {wallet_uuid} not found")
                return Response(
                    {'error': 'Wallet not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Execute operation
            if operation_type == 'DEPOSIT':
                wallet.balance += amount
                logger.info(
                    f"Deposit {amount} to wallet {wallet_uuid}. "
                    f"New balance: {wallet.balance}"
                )
            elif operation_type == 'WITHDRAW':
                if wallet.balance < amount:
                    logger.warning(
                        f"Insufficient balance for wallet {wallet_uuid}. "
                        f"Balance: {wallet.balance}, Requested: {amount}"
                    )
                    return Response(
                        {'error': 'Insufficient balance'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                wallet.balance -= amount
                logger.info(
                    f"Withdraw {amount} from wallet {wallet_uuid}. "
                    f"New balance: {wallet.balance}"
                )
            
            wallet.save()

            # Save operation to history for audit trail
            WalletOperation.objects.create(
                wallet=wallet,
                operation_type=operation_type,
                amount=amount
            )

        # Return updated wallet data
        serializer_wallet = WalletSerializer(wallet)
        return Response(
            serializer_wallet.data,
            status=status.HTTP_200_OK
        )

    except Exception as e:
        # Log unexpected errors and return generic error message
        logger.error(
            f"Error processing operation for wallet {wallet_uuid}: "
            f"{str(e)}",
            exc_info=True
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

