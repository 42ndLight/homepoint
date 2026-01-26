from rest_framework import serializers
from .models import Category, Product, Variant, Inventory, StockMovement


class InventorySerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()
    change_amount = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    movement_type = serializers.ChoiceField(choices=StockMovement.MOVEMENT_TYPES, write_only=True)
    reason = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Inventory
        fields = ['quantity', 'is_low_stock', 'change_amount', 'movement_type', 'reason']
        read_only_fields = ['quantity', 'is_low_stock']  #Customers only read


class VariantSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer(read_only=True)
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)

    class Meta:
        model = Variant
        fields = [
            'id', 'sku', 'attributes', 'price', 'unit_type',
            'unit_type_display', 'stock_threshold', 'inventory',
            'item_code','tax_type'
        ]
        read_only_fields = ['inventory']


class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'is_active', 'category', 'variants'
        ]


class CategorySerializer(serializers.ModelSerializer):   
    

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent']



class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['change_amount', 'movement_type', 'reason', 'created_at', 'user']
        read_only_fields = ['created_at', 'user']

    def validate_movement_type(self, value):
        user = self.context['request'].user
        
        # Restriction: Only Admins can use 'ADJ' (Adjustment)
        if value == 'ADJ' and not user.is_staff:
            raise serializers.ValidationError("Only administrators can perform stock adjustments.")
        
        # Staff can only do IN or OUT
        if value not in ['IN', 'OUT', 'ADJ']:
             raise serializers.ValidationError("Invalid movement type.")
             
        return value