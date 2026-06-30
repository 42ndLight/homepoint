from django.db import models, transaction
from django.contrib.auth import get_user_model
from products.models import Variant, Inventory

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid - Awaiting Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15)  # Crucial for M-Pesa STK Push
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Includes delivery markup
    delivery_location = models.CharField(max_length=200)  # Simple text for MVP

    class Meta:
            ordering = ['-id']
            indexes = [
            models.Index(fields=['user', '-created_at']),  # User's orders
            models.Index(fields=['status', '-created_at']),  # Status queries
            models.Index(fields=['phone_number']),  # Phone lookup
            models.Index(fields=['-created_at']),  # Recent orders
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.phone_number}"

    def check_items_availability(self):
        """Check all order items against Inventory in a single set of queries.

        Returns a list of shortage dicts (empty if all available).
        This avoids N+1 by loading inventories for all variants in one query.
        """
        from products.models import Inventory

        items = list(self.items.select_related('variant'))
        if not items:
            return []

        variant_ids = [it.variant_id for it in items]
        inventories = Inventory.objects.filter(variant_id__in=variant_ids).select_related('variant')
        inv_map = {inv.variant_id: inv for inv in inventories}

        shortages = []
        for it in items:
            inv = inv_map.get(it.variant_id)
            available = inv.quantity if inv is not None else 0
            if available < it.quantity:
                shortages.append({
                    'variant_id': it.variant_id,
                    'sku': getattr(it.variant, 'sku', None),
                    'requested': it.quantity,
                    'available': available,
                })

        return shortages

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot price

    class Meta:
        unique_together = ('order', 'variant')  # Prevent duplicates in same order
        indexes = [
            models.Index(fields=['order', 'variant']),  # Explicit for query planner
            models.Index(fields=['variant']),  # Variant lookups
        ]

    def __str__(self):
        return f"{self.quantity} × {self.variant.sku}"