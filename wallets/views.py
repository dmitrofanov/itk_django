import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .constants import (
    THROTTLE_READ_RATE,
    THROTTLE_WRITE_RATE,
)
from .exceptions import (
    InsufficientBalanceError,
    UnknownOperationTypeError,
    WalletNotFoundError,
)
from .models import Wallet
from .serializers import (
    WalletOperationSerializer,
    WalletSerializer
)
from .services import execute_wallet_operation

# Logger for wallet operations
logger = logging.getLogger('wallets')


class WalletReadThrottle(UserRateThrottle):
    """Throttle for wallet read operations (GET)."""
    rate = THROTTLE_READ_RATE


class WalletWriteThrottle(UserRateThrottle):
    """Throttle for wallet write operations (POST)."""
    rate = THROTTLE_WRITE_RATE


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([WalletReadThrottle])
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
@permission_classes([IsAuthenticated])
@throttle_classes([WalletWriteThrottle])
def wallet_operation(request, wallet_uuid):
    """
    Execute wallet operation (DEPOSIT or WITHDRAW).

    POST /api/v1/wallets/{WALLET_UUID}/operation

    Body:
    {
        "operation_type": "DEPOSIT" or "WITHDRAW",
        "amount": 1000
    }

    Note: operation_type values are defined in wallets.constants
    """
    # Validate input data
    serializer = WalletOperationSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            f"Invalid operation data for wallet {wallet_uuid}: "
            f"{serializer.errors}"
        )
        # Standardize error format
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    operation_type = serializer.validated_data['operation_type']
    amount = serializer.validated_data['amount']

    try:
        # Execute operation using service layer
        wallet = execute_wallet_operation(
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

    except WalletNotFoundError as e:
        return Response(
            {'errors': {'non_field_errors': [str(e)]}},
            status=status.HTTP_404_NOT_FOUND
        )

    except InsufficientBalanceError as e:
        return Response(
            {'errors': {'non_field_errors': [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST
        )

    except UnknownOperationTypeError as e:
        return Response(
            {'errors': {'non_field_errors': [str(e)]}},
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
            {'errors': {'non_field_errors': ['Internal server error']}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

