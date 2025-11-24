import logging

from django.db import transaction

from .constants import (
    OPERATION_TYPE_DEPOSIT,
    OPERATION_TYPE_WITHDRAW,
)
from .exceptions import (
    InsufficientBalanceError,
    UnknownOperationTypeError,
    WalletNotFoundError,
)
from .models import Wallet, WalletOperation

# Logger for wallet operations
logger = logging.getLogger('wallets')


@transaction.atomic
def execute_wallet_operation(wallet_uuid, operation_type, amount):
    """
    Execute wallet operation (DEPOSIT or WITHDRAW).

    Args:
        wallet_uuid: UUID of the wallet
        operation_type: OPERATION_TYPE_DEPOSIT or OPERATION_TYPE_WITHDRAW
        amount: Operation amount

    Returns:
        Wallet: Updated wallet instance

    Raises:
        WalletNotFoundError: If wallet not found
        InsufficientBalanceError: If insufficient balance for withdrawal
        UnknownOperationTypeError: If operation type is unknown
    """
    # Lock wallet row to prevent race conditions
    try:
        wallet = Wallet.objects.select_for_update().get(id=wallet_uuid)
    except Wallet.DoesNotExist:
        logger.warning(
            'Wallet not found',
            extra={
                'wallet_uuid': str(wallet_uuid),
                'operation_type': operation_type,
                'amount': str(amount),
                'error_type': 'WalletNotFoundError',
            }
        )
        raise WalletNotFoundError(f"Wallet {wallet_uuid} not found")

    # Execute operation based on type
    if operation_type == OPERATION_TYPE_DEPOSIT:
        wallet.deposit(amount)
    elif operation_type == OPERATION_TYPE_WITHDRAW:
        wallet.withdraw(amount)
    else:
        raise UnknownOperationTypeError(
            f"Unknown operation type: {operation_type}. "
            f"Expected {OPERATION_TYPE_DEPOSIT} or {OPERATION_TYPE_WITHDRAW}"
        )

    # Save wallet with updated balance
    wallet.save()

    # Save operation to history for audit trail
    WalletOperation.objects.create(
        wallet=wallet,
        operation_type=operation_type,
        amount=amount
    )

    return wallet

