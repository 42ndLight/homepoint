from rest_framework import serializers
from .models import Category, Product, Variant, Inventory, StockMovement

def get_user_role(request):
    """
    Read role directly from user.role (set by management command).
    Falls back to 'customer' for unauthenticated or unknown users.
    """
    if request is None:
        return 'customer'
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return 'customer'
    return getattr(user, 'role', 'customer')


# Roles that may see raw stock numbers and thresholds
PRIVILEGED_ROLES = {'admin', 'staff'}

class CategorySerializer(serializers.ModelSerializer):   
    

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent']

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
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)

    # Flat stock fields pulled from the related Inventory object
    stock_quantity  = serializers.SerializerMethodField()
    stock_threshold = serializers.SerializerMethodField()

    # Safe computed label — always present for cashier/fundi, stripped for customer
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Variant
        fields = [
            'id',
            'sku',
            'item_code',
            'attributes',
            'price',
            'unit_type',
            'unit_type_display',
            'tax_type',
            'stock_quantity',    # stripped for non-privileged
            'stock_threshold',   # stripped for non-privileged
            'stock_status',      # stripped for customer; label only for cashier/fundi
        ]

    def get_stock_quantity(self, obj):
        inv = getattr(obj, 'inventory', None)
        return getattr(inv, 'quantity', 0)

    def get_stock_threshold(self, obj):
        return obj.stock_threshold

    def get_stock_status(self, obj):
        inv       = getattr(obj, 'inventory', None)
        qty       = getattr(inv, 'quantity', 0) or 0
        threshold = obj.stock_threshold or 10
        if qty <= 0:
            return 'out_of_stock'
        if qty <= threshold:
            return 'low_stock'
        return 'in_stock'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        role = self.context.get('role', 'customer')

        if role not in PRIVILEGED_ROLES:
            # Remove exact numbers for all non-privileged roles
            data.pop('stock_quantity', None)
            data.pop('stock_threshold', None)

        if role == 'customer':
            # Customers don't need stock status either — they just browse
            data.pop('stock_status', None)

        return data


class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    variants = VariantSerializer(many=True, read_only=True)   

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'is_active', 'category','category_detail', 'variants'
        ]

    def get_variants(self, obj):
        # Pass role context into each VariantSerializer
        return VariantSerializer(
            obj.variants.all(),
            many=True,
            context=self.context,   # role travels through here
        ).data   



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