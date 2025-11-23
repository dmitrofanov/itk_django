import logging

from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Wallet, WalletOperation

# Logger for wallet operations
logger = logging.getLogger('wallets')


@transaction.atomic
def execute_wallet_operation(wallet_uuid, operation_type, amount):
    """
    Execute wallet operation (DEPOSIT or WITHDRAW).

    Args:
        wallet_uuid: UUID of the wallet
        operation_type: 'DEPOSIT' or 'WITHDRAW'
        amount: Operation amount

    Returns:
        Wallet: Updated wallet instance

    Raises:
        Wallet.DoesNotExist: If wallet not found
        ValidationError: If insufficient balance for withdrawal
    """
    # Lock wallet row to prevent race conditions
    try:
        wallet = Wallet.objects.select_for_update().get(id=wallet_uuid)
    except Wallet.DoesNotExist:
        logger.warning(f"Wallet {wallet_uuid} not found")
        raise

    # Execute operation based on type
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
            raise ValidationError('Insufficient balance')
        wallet.balance -= amount
        logger.info(
            f"Withdraw {amount} from wallet {wallet_uuid}. "
            f"New balance: {wallet.balance}"
        )
    else:
        raise ValueError(f"Unknown operation type: {operation_type}")

    # Save wallet with updated balance
    wallet.save()

    # Save operation to history for audit trail
    WalletOperation.objects.create(
        wallet=wallet,
        operation_type=operation_type,
        amount=amount
    )

    return wallet

