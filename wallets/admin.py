from django.contrib import admin

from .models import Wallet, WalletOperation


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin interface for Wallet model."""
    list_display = ['id', 'balance', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['id']


@admin.register(WalletOperation)
class WalletOperationAdmin(admin.ModelAdmin):
    """Admin interface for WalletOperation model."""
    list_display = [
        'id',
        'wallet',
        'operation_type',
        'amount',
        'created_at'
    ]
    readonly_fields = ['id', 'created_at']
    list_filter = ['operation_type', 'created_at']
    search_fields = ['wallet__id']


