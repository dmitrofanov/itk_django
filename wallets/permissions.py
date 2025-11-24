from django.http import Http404
from rest_framework.permissions import BasePermission

from .models import Wallet


class IsWalletOwner(BasePermission):
    """
    Permission that ensures the authenticated user owns the wallet referenced
    in the request. Raises Http404 when the wallet does not exist or is not
    associated with the requesting user to avoid leaking UUIDs.
    """

    message = 'You do not have permission to access this wallet.'

    def has_permission(self, request, view):
        wallet_uuid = self._get_wallet_uuid(request, view)
        if not wallet_uuid:
            # Endpoint without wallet UUID parameter.
            return True

        if request.user.is_anonymous:
            return False

        try:
            wallet = Wallet.objects.only('id', 'user_id').get(
                id=wallet_uuid,
                user=request.user,
            )
        except Wallet.DoesNotExist as exc:
            raise Http404('Wallet not found') from exc

        # Attach wallet to the request for downstream consumers.
        request.wallet = wallet
        return True

    @staticmethod
    def _get_wallet_uuid(request, view):
        if hasattr(view, 'kwargs'):
            return view.kwargs.get('wallet_uuid')

        parser_kwargs = getattr(request, 'parser_context', {}).get('kwargs')
        if parser_kwargs:
            return parser_kwargs.get('wallet_uuid')

        return request.resolver_match.kwargs.get('wallet_uuid') if request.resolver_match else None

