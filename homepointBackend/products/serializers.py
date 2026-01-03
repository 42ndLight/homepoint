from rest_framework import serializers
from .models import Category, Product, Variant, Inventory


class InventorySerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Inventory
        fields = ['quantity', 'is_low_stock']
        #read_only_fields = ['quantity', 'is_low_stock']  Customers only read


class VariantSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer(read_only=True)
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)

    class Meta:
        model = Variant
        fields = [
            'id', 'sku', 'attributes', 'price', 'unit_type',
            'unit_type_display', 'stock_threshold', 'inventory'
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
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'products']