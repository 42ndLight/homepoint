from django.contrib import admin

from .models import Order, OrderItem

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at', 'delivery_location')
    search_fields = ('user__username', 'user__email', 'status')
    list_filter = ('status', 'created_at')  


class OrderItemInline(admin.TabularInline):
    
    
    list_display = ('variant', 'quantity', 'price_at_purchase')
    readonly_fields = ('variant', 'quantity', 'price_at_purchase')
    search_fields = ('order__id')
    can_delete = False
    

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)  