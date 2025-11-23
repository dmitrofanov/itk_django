"""
Custom exceptions for wallets app.

These exceptions represent business logic errors and should be used
in the service layer instead of generic Django exceptions.
"""


class WalletError(Exception):
    """Base exception for wallet-related errors."""
    pass


class WalletNotFoundError(WalletError):
    """Raised when wallet is not found."""
    pass


class InsufficientBalanceError(WalletError):
    """Raised when wallet has insufficient balance for operation."""
    pass


class UnknownOperationTypeError(WalletError):
    """Raised when operation type is unknown."""
    pass

