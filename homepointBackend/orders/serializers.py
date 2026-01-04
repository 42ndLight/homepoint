from rest_framework import serializers
from products.models import Variant, Inventory
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=Variant.objects.all(), source='variant', write_only=True
    )
    sku = serializers.CharField(source='variant.sku', read_only=True)
    unit_type = serializers.CharField(source='variant.unit_type_display', read_only=True)
    price = serializers.DecimalField(
        source='variant.price', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['variant_id', 'quantity', 'sku', 'unit_type', 'price', 'price_at_purchase']
        read_only_fields = ['price_at_purchase']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    phone_number = serializers.CharField(max_length=15)
    delivery_location = serializers.CharField(max_length=200)

    class Meta:
        model = Order
        fields = ['phone_number', 'delivery_location', 'items', 'total_amount']
        read_only_fields = ['total_amount']

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'phone_number', 'delivery_location', 'total_amount',
                  'status', 'created_at', 'items']
        read_only_fields = ['id', 'total_amount', 'status', 'created_at']