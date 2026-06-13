from django.db.models import Q
from rest_framework import viewsets, filters, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from ..permissions import IsWarehouseStaff
from ..models import Category, Product, Variant, Inventory, StockMovement
from ..serializers import (
    CategorySerializer, ProductSerializer,
    VariantSerializer, InventorySerializer, get_user_role
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


class CategoryViewSet(FullCRUDViewSet):
    queryset = Category.objects.all().prefetch_related(
        'products__variants__inventory' 
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProductViewSet(FullCRUDViewSet):
    queryset = Product.objects.filter(is_active=True).prefetch_related(
        'variants__inventory'
    )
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['base_price']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class VariantViewSet(FullCRUDViewSet):
    queryset = Variant.objects.select_related('product').prefetch_related('inventory')
    serializer_class = VariantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['sku', 'attributes']


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

