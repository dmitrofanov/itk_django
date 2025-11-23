from django.urls import path

from . import views

app_name = 'wallets'

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


