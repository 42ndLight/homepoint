from django.contrib import admin
from .models import Category, Product, Variant, Inventory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}  # Auto-fill slug


class InventoryInline(admin.TabularInline):
    model = Inventory
    extra = 0
    readonly_fields = ['last_updated']
    fields = ['quantity', 'location']


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1  # Allow adding new variants easily
    fields = ['sku', 'attributes', 'price', 'unit_type', 'stock_threshold']
    inlines = [InventoryInline]  # Nested: edit inventory on variant


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'base_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [VariantInline]  # Add/edit variants + inventory right here


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'price', 'unit_type', 'quantity_in_stock']
    list_filter = ['unit_type', 'product__category']
    search_fields = ['sku', 'product__name', 'attributes']

    def quantity_in_stock(self, obj):
        return obj.inventory.quantity if hasattr(obj, 'inventory') else 0
    quantity_in_stock.short_description = 'Stock Quantity'

    inlines = [InventoryInline]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['variant', 'quantity', 'is_low_stock', 'last_updated', 'location']
    list_filter = ['last_updated']
    search_fields = ['variant__sku', 'variant__product__name']