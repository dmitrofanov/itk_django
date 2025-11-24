import logging

from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
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


def _get_user_wallet_or_404(user, wallet_uuid):
    wallet = Wallet.objects.filter(id=wallet_uuid, user=user).first()
    if wallet is None:
        raise Http404('Wallet not found')
    return wallet


@extend_schema(
    summary='Get wallet information',
    description='Retrieve wallet information including balance by wallet UUID',
    responses={
        200: WalletSerializer,
        404: OpenApiResponse(description='Wallet not found'),
        401: OpenApiResponse(description='Authentication required'),
        429: OpenApiResponse(description='Rate limit exceeded'),
    },
    parameters=[
        OpenApiParameter(
            name='wallet_uuid',
            type=str,
            location=OpenApiParameter.PATH,
            description='Wallet UUID',
            required=True,
        ),
    ],
    tags=['Wallets'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([WalletReadThrottle])
def wallet_detail(request, wallet_uuid):
    """
    Get wallet information by UUID.

    GET /api/v1/wallets/{WALLET_UUID}
    """
    wallet = _get_user_wallet_or_404(request.user, wallet_uuid)
    serializer = WalletSerializer(wallet)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary='Execute wallet operation',
    description='Execute DEPOSIT (add) or WITHDRAW (subtract) operation on wallet',
    request=WalletOperationSerializer,
    responses={
        200: WalletSerializer,
        400: OpenApiResponse(description='Bad request - validation error or insufficient balance'),
        404: OpenApiResponse(description='Wallet not found'),
        401: OpenApiResponse(description='Authentication required'),
        429: OpenApiResponse(description='Rate limit exceeded'),
    },
    parameters=[
        OpenApiParameter(
            name='wallet_uuid',
            type=str,
            location=OpenApiParameter.PATH,
            description='Wallet UUID',
            required=True,
        ),
    ],
    tags=['Wallets'],
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
    wallet = _get_user_wallet_or_404(request.user, wallet_uuid)

    # Validate input data
    serializer = WalletOperationSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(
            'Invalid operation data',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'user_id': request.user.id,
                'endpoint': 'wallet_operation',
                'errors': serializer.errors,
            }
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
            wallet_uuid=wallet.id,
            operation_type=operation_type,
            amount=amount
        )

        logger.info(
            'Operation completed successfully',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'user_id': request.user.id,
                'operation_type': operation_type,
                'amount': str(amount),
                'new_balance': str(wallet.balance),
                'endpoint': 'wallet_operation',
            }
        )

        # Return updated wallet data
        serializer_wallet = WalletSerializer(wallet)
        return Response(
            serializer_wallet.data,
            status=status.HTTP_200_OK
        )

    except WalletNotFoundError as e:
        logger.warning(
            'Wallet not found',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'user_id': request.user.id,
                'operation_type': operation_type,
                'amount': str(amount),
                'endpoint': 'wallet_operation',
                'error_type': 'WalletNotFoundError',
            }
        )
        return Response(
            {'errors': {'non_field_errors': [str(e)]}},
            status=status.HTTP_404_NOT_FOUND
        )

    except InsufficientBalanceError as e:
        logger.warning(
            'Insufficient balance',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'user_id': request.user.id,
                'operation_type': operation_type,
                'amount': str(amount),
                'endpoint': 'wallet_operation',
                'error_type': 'InsufficientBalanceError',
            }
        )
        return Response(
            {'errors': {'non_field_errors': [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST
        )

    except UnknownOperationTypeError as e:
        logger.warning(
            'Unknown operation type',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'user_id': request.user.id,
                'operation_type': operation_type,
                'amount': str(amount),
                'endpoint': 'wallet_operation',
                'error_type': 'UnknownOperationTypeError',
            }
        )
        return Response(
            {'errors': {'non_field_errors': [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        logger.error(
            'Unexpected error processing operation',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'user_id': request.user.id,
                'operation_type': operation_type,
                'amount': str(amount),
                'endpoint': 'wallet_operation',
                'error_type': type(e).__name__,
                'error_message': str(e),
            },
            exc_info=True
        )
        return Response(
            {'errors': {'non_field_errors': ['Internal server error']}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

