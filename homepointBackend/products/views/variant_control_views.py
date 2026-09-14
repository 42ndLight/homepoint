# variant_control_views.py

from rest_framework import viewsets, filters, status, mixins
from django.db.models import Prefetch
from django.core.cache import cache

from users.permissions import IsWarehouseStaff
from ..models import Variant
from ..serializers import VariantSerializer, get_user_role
from ..utils.cache_keys import get_variants_list_key, invalidate_product_cache, invalidate_variant_cache
from products.views.product_base import  CachedListRetrieveMixin, FullCRUDViewSet


class VariantViewSet(CachedListRetrieveMixin, FullCRUDViewSet):
    serializer_class = VariantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['sku', 'attributes']

    def get_queryset(self):
        return Variant.objects.select_related(
            'product'
        ).prefetch_related(
            'inventory',
            'images'
        )

    def list(self, request, *args, **kwargs):
        """Cache variant list for 5 minutes."""
        cache_key = get_variants_list_key(request.query_params)
        return self.cached_list(cache_key, 300, request, *args, **kwargs)

    def perform_create(self, serializer):
        """Invalidate cache on create."""
        serializer.save()
        invalidate_variant_cache()
        invalidate_product_cache()

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        serializer.save()
        invalidate_variant_cache()
        invalidate_product_cache()

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        instance.delete()
        invalidate_variant_cache()
        invalidate_product_cache()
