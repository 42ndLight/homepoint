# category_control_views.py

from django.db.models import Prefetch
from django.core.cache import cache
from rest_framework import filters

from users.permissions import IsWarehouseStaff
from ..models import Category
from ..serializers import CategorySerializer
from products.views.product_base import  CachedListRetrieveMixin, FullCRUDViewSet
from ..utils.cache_keys import (
    get_categories_list_key, get_category_detail_key,
    invalidate_category_cache,
)

class CategoryViewSet(CachedListRetrieveMixin, FullCRUDViewSet):
    queryset = Category.objects.all().prefetch_related(
        'products__variants__inventory',
        'products__images'
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def list(self, request, *args, **kwargs):
        """Cache category list for 5 minutes."""
        cache_key = get_categories_list_key(request.query_params)
        return self.cached_list(cache_key, 300, request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Cache individual category for 10 minutes."""
        slug = kwargs.get('slug')
        cache_key = get_category_detail_key(slug)
        return self.cached_retrieve(cache_key, 600, request, *args, **kwargs)

    def perform_create(self, serializer):
        """Invalidate cache on create."""
        serializer.save()
        invalidate_category_cache()

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        instance = serializer.save()
        invalidate_category_cache()
        cache.delete(get_category_detail_key(instance.slug))

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        slug = instance.slug
        instance.delete()
        invalidate_category_cache()
        cache.delete(get_category_detail_key(slug))