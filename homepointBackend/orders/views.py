from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from .models import Order, OrderItem
from django.db.models import Prefetch
from .serializers import OrderCreateSerializer, OrderDetailSerializer
from users.permissions import IsWarehouseStaff

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly | IsWarehouseStaff ]  # Allow guest checkout via phone

    def get_queryset(self):
        queryset = Order.objects.select_related(
            'user'
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('variant__product', 'variant__inventory')
            ),
            'cash_transactions',
            'mpesa_transactions',
            'paystack_transactions',
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

    @action(detail=True, methods=['post'], url_path='complete-mpesa', permission_classes=[IsWarehouseStaff])
    def complete_mpesa(self, request, pk=None):
        """
        Manually record a confirmed M-Pesa payment (e.g. staff reconciling a
        receipt number reported by the customer) and mark the order paid.
        """
        order = self.get_object()
        mpesa_receipt_number = (request.data.get('mpesa_receipt_number') or '').strip()
        phone_number = (request.data.get('phone_number') or '').strip()

        if not mpesa_receipt_number or not phone_number:
            return Response(
                {"detail": "mpesa_receipt_number and phone_number are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status == 'paid':
            return Response({"detail": f"Order #{order.id} is already marked as paid."},
                             status=status.HTTP_400_BAD_REQUEST)

        from payments.services import record_mpesa_sale
        import uuid

        try:
            record_mpesa_sale(
                user=request.user,
                order=order,
                amount=order.total_amount,
                phone_number=phone_number,
                checkout_request_id=f"MANUAL-{uuid.uuid4().hex[:12]}",
                mpesa_receipt=mpesa_receipt_number,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        response_serializer = OrderDetailSerializer(order)
        return Response({
            "message": "M-Pesa payment completed successfully",
            "order": response_serializer.data,
        }, status=status.HTTP_200_OK)