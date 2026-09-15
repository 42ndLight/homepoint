from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.core.cache import cache

from users.permissions import IsWarehouseStaff
from products.serializers import get_user_role

class BaseProductViewSet(viewsets.GenericViewSet):
    """
    Base ViewSet for products that handles permissions and context logic.
    Read-only for authenticated users, full CRUD for admins and warehouse staff.
    """
    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        # Use class references for bitwise operator |
        return [(IsAdminUser | IsWarehouseStaff)()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['role'] = get_user_role(self.request)
        return context

class FullCRUDViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      BaseProductViewSet):
    """
    Generic ViewSet that provides standard CRUD actions.
    """
    pass


class CachedListRetrieveMixin:
    """Shared helper for caching list and retrieve views."""
    def cached_list(self, cache_key, timeout, request, *args, **kwargs):
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout)
        return response

    def cached_retrieve(self, cache_key, timeout, request, *args, **kwargs):
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout)
        return response


