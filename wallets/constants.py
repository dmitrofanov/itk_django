"""
Constants for wallets app.

This module contains all configuration constants used throughout the application
to avoid magic numbers and improve maintainability.
"""
from decimal import Decimal

# Decimal field configuration
DECIMAL_MAX_DIGITS = 20
DECIMAL_PLACES = 2

# Balance configuration
WALLET_MIN_BALANCE = Decimal('0.00')
WALLET_DEFAULT_BALANCE = Decimal('0.00')

# Operation configuration
OPERATION_MIN_AMOUNT = Decimal('0.01')
OPERATION_TYPE_MAX_LENGTH = 10

# Operation types
OPERATION_TYPE_DEPOSIT = 'DEPOSIT'
OPERATION_TYPE_WITHDRAW = 'WITHDRAW'

# Throttling configuration
THROTTLE_READ_LIMIT = 200  # Number of GET requests per hour
THROTTLE_WRITE_LIMIT = 100  # Number of POST requests per hour
THROTTLE_READ_RATE = f'{THROTTLE_READ_LIMIT}/hour'  # GET requests limit
THROTTLE_WRITE_RATE = f'{THROTTLE_WRITE_LIMIT}/hour'  # POST requests limit

