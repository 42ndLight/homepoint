from rest_framework import serializers
from products.models import Variant, Inventory
from .models import Order, OrderItem
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    net_amount = serializers.SerializerMethodField()
    vat_amount = serializers.SerializerMethodField()
    vat_rate = serializers.SerializerMethodField()

    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=Variant.objects.all(), source='variant', write_only=True
    )
    sku = serializers.CharField(source='variant.sku', read_only=True)
    unit_type = serializers.CharField(source='variant.unit_type', read_only=True)
    price = serializers.DecimalField(
        source='variant.price', max_digits=10, decimal_places=2, read_only=True
    )
    item_code = serializers.CharField(source='variant.item_code', read_only=True)
    tax_type = serializers.CharField(source='variant.tax_type', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'variant_id', 'quantity', 'sku', 'unit_type', 'price',
            'net_amount', 'vat_amount', 'vat_rate',
            'price_at_purchase', 'item_code','tax_type']
        read_only_fields = ['price_at_purchase']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    # 1. Calculate Net Amount (Price without VAT)
    def get_net_amount(self, obj):
        # Using the logic: Net = Total / 1.16
        rate = Decimal('0.16') if obj.variant.tax_type == 'A' else Decimal('0.00')
        if rate == 0:
            return Decimal('0.00')
        else:
            net_unit_price = obj.price_at_purchase / (1 + rate)
        return round(net_unit_price * obj.quantity, 2)

    # 2. Calculate VAT Amount
    def get_vat_amount(self, obj):
        total = obj.price_at_purchase * obj.quantity
        net = self.get_net_amount(obj)
        return round(total - net, 2)

    # 3. Report VAT Rate as a string for eTIMS
    def get_vat_rate(self, obj):
        return "16%" if obj.variant.tax_type == 'A' else "0%"

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