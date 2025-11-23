import logging

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Wallet
from .serializers import (
    WalletOperationSerializer,
    WalletSerializer
)
from .services import WalletService

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
        # Execute operation using service layer
        wallet = WalletService.execute_operation(
            wallet_uuid=wallet_uuid,
            operation_type=operation_type,
            amount=amount
        )

        # Return updated wallet data
        serializer_wallet = WalletSerializer(wallet)
        return Response(
            serializer_wallet.data,
            status=status.HTTP_200_OK
        )

    except Wallet.DoesNotExist:
        return Response(
            {'error': 'Wallet not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    except ValidationError as e:
        # ValidationError always has messages attribute (list)
        # In our service, we always raise ValidationError with a simple string
        error_message = str(e.messages[0]) if e.messages else str(e)
        return Response(
            {'error': error_message},
            status=status.HTTP_400_BAD_REQUEST
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

