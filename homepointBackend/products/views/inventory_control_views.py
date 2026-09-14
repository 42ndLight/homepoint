# inventory_control_view.py

from rest_framework import status, mixins
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F

from ..models import Variant, StockMovement
from ..serializers import InventorySerializer
from products.views.product_base import  CachedListRetrieveMixin, FullCRUDViewSet, BaseProductViewSet


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