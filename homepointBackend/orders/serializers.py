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
    product_name = serializers.CharField(source='variant.product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'variant_id', 'quantity', 'sku', 'unit_type', 'price',
            'net_amount', 'vat_amount', 'vat_rate',
            'price_at_purchase', 'item_code','tax_type', 'product_name']
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
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'phone_number', 'delivery_location', 'total_amount',
                  'status', 'created_at', 'items', 'payment']
        read_only_fields = ['id', 'total_amount', 'status', 'created_at', 'payment']

    # Canonical, receipt-facing payment summary. Only ever reports the newest
    # SUCCESSFUL transaction for the order — pending/failed attempts must
    # never be surfaced as receipt payment data.
    def get_payment(self, obj):
        candidates = []

        for cash_tx in obj.cash_transactions.all():
            if cash_tx.status == 'SUCCESS':
                candidates.append({
                    'method': 'cash',
                    'method_display': 'Cash',
                    'status': cash_tx.status,
                    'reference': cash_tx.receipt_number or None,
                    'paid_at': cash_tx.created_at,
                })

        for mpesa_tx in obj.mpesa_transactions.all():
            if mpesa_tx.status == 'SUCCESS':
                candidates.append({
                    'method': 'mpesa',
                    'method_display': 'M-Pesa',
                    'status': mpesa_tx.status,
                    'reference': mpesa_tx.mpesa_receipt_number or None,
                    'paid_at': mpesa_tx.timestamp,
                })

        for paystack_tx in obj.paystack_transactions.all():
            if paystack_tx.status == 'SUCCESS':
                candidates.append({
                    'method': 'paystack',
                    'method_display': 'Card',
                    'status': paystack_tx.status,
                    'reference': paystack_tx.paystack_reference or None,
                    'paid_at': paystack_tx.timestamp,
                })

        if not candidates:
            return None

        latest = max(candidates, key=lambda c: c['paid_at'])
        latest = {**latest, 'paid_at': latest['paid_at'].strftime('%Y-%m-%d %H:%M') if latest['paid_at'] else None}
        return latest