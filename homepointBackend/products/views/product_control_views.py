# product_control.py
from django.db.models import Q
from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from rest_framework.decorators import action
from django.core.cache import cache
from rest_framework.response import Response

from ..models import Product, Variant
from ..serializers import (
     ProductSerializer, get_user_role
)
from ..utils.cache_keys import (
    get_products_list_key, get_product_detail_key,
    invalidate_category_cache, invalidate_product_cache
)
from products.views.product_base import  CachedListRetrieveMixin, FullCRUDViewSet

class ProductViewSet(CachedListRetrieveMixin, FullCRUDViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['base_price']

    def get_queryset(self):
        variant_prefetch = Prefetch(
            'variants',
            Variant.objects.prefetch_related(
                'inventory',
                'images'
            )
        )
        queryset = Product.objects.filter(is_active=True).prefetch_related(
            variant_prefetch,
            'images' 
        ).select_related('category')

        category_id = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset

    def list(self, request, *args, **kwargs):
        """Cache product list for 5 minutes, scoped by user role."""
        role = get_user_role(request)
        cache_key = get_products_list_key(request.query_params, role)
        return self.cached_list(cache_key, 300, request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Cache individual product for 10 minutes."""
        slug = kwargs.get('slug')
        role = get_user_role(request)
        cache_key = get_product_detail_key(slug, role)
        return self.cached_retrieve(cache_key, 600, request, *args, **kwargs)

    def perform_create(self, serializer):
        """Invalidate cache on create."""
        serializer.save()
        invalidate_product_cache()
        invalidate_category_cache()

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        instance = serializer.save()
        invalidate_product_cache()
        cache.delete(get_product_detail_key(instance.slug))
        invalidate_category_cache()

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        slug = instance.slug
        instance.delete()
        invalidate_product_cache()
        cache.delete(get_product_detail_key(slug))
        invalidate_category_cache()

    @action(detail=False, methods=['get'], url_path='dump',
            permission_classes=[IsAuthenticated])
    def dump(self, request):
        """
        GET /products/products/dump/
        Returns every active product with all variants and inventory — no pagination.
        Intended for the offline sync service and full catalog refresh.
        Cached for 5 minutes per role; busted on any import or product write.
        """
        role = get_user_role(request)
        cache_key = f'products:dump:role:{role}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        variant_prefetch = Prefetch(
            'variants',
            Variant.objects.prefetch_related('inventory', 'images')
        )
        queryset = (
            Product.objects
            .filter(is_active=True)
            .prefetch_related(variant_prefetch, 'images')
            .select_related('category')
            .order_by('id')
        )
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(cache_key, data, 300)
        return Response(data)