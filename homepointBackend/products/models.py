from django.db import models
from django.utils.text import slugify
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "Pipes", "Boards", "Doors"
    slug = models.SlugField(max_length=100, unique=True, blank=True)  # Auto-generated for URLs
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')  # For hierarchy, e.g., "Building Materials" > "Pipes"
    description = models.TextField(blank=True)  # Optional short desc for SEO/UI

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)  # e.g., "PVC Pipe", "MDF Board"
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # For pretty URLs
    description = models.TextField()  # Detailed info, materials, usage tips for fundis
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting price in KES")  # For display; variants override
    is_active = models.BooleanField(default=True)

    class Meta:
            ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', null=True, blank=True)

class Variant(models.Model):
    UNIT_CHOICES = [
        ('piece', 'Per Piece'),  # e.g., doors
        ('meter', 'Per Meter'),  # e.g., pipes
        ('kg', 'Per Kg'),  # e.g., nails or fittings
        ('sqm', 'Per Square Meter'),  # e.g., boards/tiles
        # Add more as needed, e.g., 'bundle', 'liter'
    ]
    TAX_CHOICES = [
        ('A', '16% VAT (Standard)'),
        ('B', '0% VAT (Zero-rated)'),
        ('C', 'Exempt'),
        # Add 'D' for Non-VAT if applicable
    ]    

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=50, unique=True)  # Unique identifier, e.g., "PVC-1IN-3M"
    attributes = models.JSONField(default=dict)  # Flexible: {'diameter': '1 inch', 'length': '3m', 'color': 'white'}
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in KES, includes delivery markup")
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    stock_threshold = models.PositiveIntegerField(default=10)  # Low-stock alert trigger
    item_code = models.CharField(max_length=50, help_text="HS Code / eTIMS Item Code")
    tax_type = models.CharField(max_length=2, choices=TAX_CHOICES, default='A')

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

class VariantImage(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='variants/', null=True, blank=True)

class Inventory(models.Model):
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)  # Current stock level
    last_updated = models.DateTimeField(auto_now=True)  # For tracking changes
    location = models.CharField(max_length=100, blank=True)  # Optional: e.g., "Nairobi Warehouse" for multi-location later

    def __str__(self):
        return f"Inventory for {self.variant.sku}: {self.quantity} units"

    def is_low_stock(self):
        return self.quantity <= self.variant.stock_threshold

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In (Restock)'),
        ('OUT', 'Stock Out (Sale)'),
        ('ADJ', 'Adjustment (Damage/Correction)'),
    ]

    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE, related_name='movements')
    variant = models.ForeignKey('Variant', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    change_amount = models.DecimalField(max_digits=10, decimal_places=2) # e.g., +10 or -5
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']