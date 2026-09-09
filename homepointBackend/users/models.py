# models.py (update from our previous schema)
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group, Permission, UserManager
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)


        if extra_fields.get('role') != 'admin':
            raise ValueError('Superuser must have role="admin".')

        if not extra_fields.get('phone_number'):
            raise ValueError('Superuser must have a phone number.')

        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    objects = CustomUserManager()

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('fundi', 'Fundi'),
        ('customer', 'Customer'),
    )
    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(
        max_length=15, unique=True, 
        help_text="Kenyan phone for M-Pesa/OTP"
    )
    is_verified = models.BooleanField(default=False)  # OTP/SMS verification
    last_activity = models.DateTimeField(null=True, blank=True)  # For staff daily logs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='users_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='users_set',
        blank=True
    )
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        indexes = [
        models.Index(fields=['role', 'phone_number']),
        models.Index(fields=['email']),  # Email login
        models.Index(fields=['username']),  # Username login
        models.Index(fields=['is_staff', 'is_active']),
        ]
        permissions = [  # Custom perms for RBAC
            ("can_manage_inventory", "Can add/edit/delete inventory"),
            ("can_view_sales", "Can view orders and sales"),
            ("can_approve_fundi", "Can approve fundi profiles"),
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff_member(self):
        return self.role in ['admin', 'staff']

    def get_otp_cache_key(self, intent="login"):
        return f"{intent}_otp_{self.phone_number}"

# Profile models (one-to-one for extensions)
class FundiProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fundi_profile')
    trade = models.CharField(max_length=100)  # e.g., Plumber, Electrician
    location = models.CharField(max_length=100)
    whatsapp_contact = models.CharField(max_length=15, blank=True)
    portfolio_images = models.JSONField(default=list)  # Store URLs for work showcases
    bio = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    is_approved = models.BooleanField(default=False)  # Admin/staff approval
    is_complete = models.BooleanField(default=False)  # Track post-login completion

class StaffProfile(models.Model):  # Minimal, for daily activity extensions if needed
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    shift_start = models.TimeField(null=True)  # For logging daily activities


class SmsNotification(models.Model):
    """An outbound SMS tracked by the provider message ID for DLR updates."""

    provider_message_id = models.CharField(max_length=255, unique=True)
    recipient = models.CharField(max_length=32)
    intent = models.CharField(max_length=32, null=True, blank=True)
    status = models.CharField(max_length=64, default='PENDING')
    network_code = models.CharField(max_length=32, blank=True)
    failure_reason = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    response_metadata = models.JSONField(default=dict, blank=True)
    delivery_reported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['provider_message_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.provider_message_id} ({self.recipient})'


# Signal to auto-create profiles
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'fundi':
            FundiProfile.objects.create(user=instance)
        elif instance.role == 'staff':
            StaffProfile.objects.create(user=instance)

@receiver(pre_save, sender=User)
def _capture_old_role(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_role = sender.objects.get(pk=instance.pk).role
        except sender.DoesNotExist:
            instance._old_role = None

@receiver(post_save, sender=User)
def assign_role_group(sender, instance, created, **kwargs):
    old_role = getattr(instance, "_old_role", None)
    if not created and old_role == instance.role:
        return  # nothing changed

    # Map user role values to the canonical Group names used in the system.
    # This runs on create and on update so role changes keep group membership in sync.
    role_to_group = {
        'staff': 'Warehouse Staff',
        'admin': 'Warehouse Staff',
        'fundi': 'Fundi',
        'customer': 'Customer',
    }

    group_name = role_to_group.get(instance.role)
    if not group_name:
        return

    # Ensure the target group exists and add the user to it.
    group, _ = Group.objects.get_or_create(name=group_name)
    if not instance.groups.filter(pk=group.pk).exists():
        instance.groups.add(group)

    # Remove the user from other role-related groups so membership stays consistent.
    other_group_names = [n for n in set(role_to_group.values()) if n != group_name]
    if other_group_names:
        other_groups = Group.objects.filter(name__in=other_group_names)
        instance.groups.remove(*other_groups)