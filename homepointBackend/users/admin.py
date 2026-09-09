from django.contrib import admin
from .models import SmsNotification, User

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'role')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'role')

admin.site.register(User, UserAdmin)


@admin.register(SmsNotification)
class SmsNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'provider_message_id', 'recipient', 'intent', 'status',
        'network_code', 'retry_count', 'created_at', 'delivery_reported_at',
    )
    list_filter = ('status', 'intent', 'created_at')
    search_fields = ('provider_message_id', 'recipient')
    readonly_fields = ('created_at', 'updated_at', 'delivery_reported_at')