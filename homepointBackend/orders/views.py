from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from .models import Order, OrderItem
from django.db.models import Prefetch
from .serializers import OrderCreateSerializer, OrderDetailSerializer

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allow guest checkout via phone

    def get_queryset(self):
        queryset = Order.objects.select_related(
            'user'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('variant__product', 'variant__inventory')
            )
        )

        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return queryset.all()
            return queryset.filter(user=self.request.user)
        return queryset.none()

    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer

    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data.pop('items')
        phone_number = serializer.validated_data['phone_number']

        # Lock relevant inventory rows
        from products.models import Inventory
        variant_ids = [item['variant'].id for item in items_data]
        inventories = Inventory.objects.select_for_update().filter(variant_id__in=variant_ids)

        # Build stock map
        stock_map = {inv.variant_id: inv.quantity for inv in inventories}
        insufficient = []

        total_amount = 0
        order_items_to_create = []

        for item in items_data:
            variant = item['variant']
            qty = item['quantity']
            available = stock_map.get(variant.id, 0)

            if available < qty:
                insufficient.append(f"{variant.sku}: requested {qty}, available {available}")
                continue

            total_amount += variant.price * qty
            order_items_to_create.append(OrderItem(
                variant=variant,
                quantity=qty,
                price_at_purchase=variant.price
            ))

        if insufficient:
            return Response({
                "detail": "Insufficient stock for some items",
                "errors": insufficient
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            phone_number=phone_number,
            delivery_location=serializer.validated_data['delivery_location'],
            total_amount=total_amount,
            status='pending'
        )

        # Bulk create items
        for item in order_items_to_create:
            item.order = order
        OrderItem.objects.bulk_create(order_items_to_create)

        # Atomically deduct stock using F expressions (safe under row lock)
        for item in order_items_to_create:
            Inventory.objects.filter(variant=item.variant).update(
                quantity=F('quantity') - item.quantity
            )

        # Serialize response
        response_serializer = OrderDetailSerializer(order)
        return Response({
            "message": "Order created successfully. Proceed to M-Pesa payment.",
            "order": response_serializer.data
        }, status=status.HTTP_201_CREATED)