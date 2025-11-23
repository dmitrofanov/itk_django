from django.urls import path

from . import views

app_name = 'wallets'

# URL patterns for wallet API v1
# More specific routes must come before less specific ones
urlpatterns = [
    path(
        'wallets/<uuid:wallet_uuid>/operation/',
        views.wallet_operation,
        name='wallet-operation'
    ),
    path(
        'wallets/<uuid:wallet_uuid>/',
        views.wallet_detail,
        name='wallet-detail'
    ),
]


