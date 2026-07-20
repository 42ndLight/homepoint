from django.db.models import Q
from rest_framework import viewsets, filters, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from django.db.models import Prefetch
from django.core.cache import cache

from ..permissions import IsWarehouseStaff
from ..models import Category, Product, Variant, Inventory, StockMovement
from ..serializers import (
    CategorySerializer, ProductSerializer,
    VariantSerializer, InventorySerializer, get_user_role
)
from ..utils.cache_keys import (
    get_categories_list_key, get_category_detail_key,
    get_products_list_key, get_product_detail_key,
    get_variants_list_key,
    invalidate_category_cache, invalidate_product_cache, invalidate_variant_cache
)

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


class InventoryViewSet(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       BaseProductViewSet):
    """
    Simple endpoint for stock checks (public read) and admin updates.
    GET   /api/inventory/<variant_id>/   → public stock quantity
    PATCH /api/inventory/<variant_id>/   → admin only: update stock
    """
    serializer_class = InventorySerializer

    def retrieve(self, request, pk=None):
        variant = get_object_or_404(Variant.objects.select_related('inventory'), pk=pk)
        serializer = InventorySerializer(variant.inventory)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """
        Custom partial update logic for inventory movement.
        """
        variant = get_object_or_404(Variant.objects.select_related('inventory'), pk=pk)
        inventory = variant.inventory
        serializer = InventorySerializer(inventory, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            with transaction.atomic():
                change = serializer.validated_data['change_amount']
                m_type = serializer.validated_data['movement_type']

                if m_type == "IN":
                    inventory.quantity = F('quantity') + change
                else:
                    inventory.quantity = F('quantity') - change
                
                inventory.save()
                
                StockMovement.objects.create(
                    inventory=inventory,
                    variant=variant,
                    user=request.user,
                    change_amount=change,
                    movement_type=m_type,
                    reason=request.data.get('reason', '')
                )

                inventory.refresh_from_db()

            serializer = InventorySerializer(inventory)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
