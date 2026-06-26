# Homepoint Backend Performance Refactoring Plan

**Project:** 42ndLight/homepoint  
**Target:** Optimize Django backend for e-commerce POS workload  
**Timeline:** 6 phases, ~4-6 weeks  
**Priority:** Address N+1 queries → caching → async processing → monitoring

---

## Executive Summary

Your backend has a solid foundation but leaves 30-40% of performance on the table. Key issues:
- **N+1 queries** in list endpoints (especially products, categories, orders)
- **No caching layer** despite Redis in dependencies
- **Image processing blocks requests** (should be async)
- **Missing database indexes** on hot columns
- **No monitoring** of query performance in production

This plan addresses each systematically, with code changes, testing instructions, and rollout strategy.

---

# PHASE 1: Database Query Optimization (Week 1)

## 1.1 Add Database Indexes

**Why:** Queries on `user_id`, `status`, `created_at`, `variant_id` are table scans without indexes.

### Changes Required

**File:** `homepointBackend/products/models.py`

```python
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['parent', 'name']),  # For subcategory lookups
            models.Index(fields=['slug']),  # Already unique, but explicit for query planner
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Starting price in KES")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['category', 'is_active']),  # Filter by category
            models.Index(fields=['is_active', '-id']),  # List active products
            models.Index(fields=['slug']),  # Slug lookups
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Variant(models.Model):
    UNIT_CHOICES = [
        ('piece', 'Per Piece'),
        ('meter', 'Per Meter'),
        ('kg', 'Per Kg'),
        ('sqm', 'Per Square Meter'),
    ]
    TAX_CHOICES = [
        ('A', '16% VAT (Standard)'),
        ('B', '0% VAT (Zero-rated)'),
        ('C', 'Exempt'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=50, unique=True)
    attributes = models.JSONField(default=dict)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    stock_threshold = models.PositiveIntegerField(default=10)
    item_code = models.CharField(max_length=50)
    tax_type = models.CharField(max_length=2, choices=TAX_CHOICES, default='A')

    class Meta:
        indexes = [
            models.Index(fields=['product', 'sku']),  # Variant lookups
            models.Index(fields=['sku']),  # Direct SKU search
            models.Index(fields=['product', 'price']),  # Price filtering
        ]

    def __str__(self):
        return f"{self.product.name} - {self.sku}"


class Inventory(models.Model):
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['variant']),  # OneToOne already indexed, but explicit
        ]

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
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2)
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory', '-created_at']),  # Audit trail
            models.Index(fields=['user', '-created_at']),  # User activity
            models.Index(fields=['movement_type', '-created_at']),  # Movement type filter
        ]
```

**File:** `homepointBackend/orders/models.py`

```python
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

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_location = models.CharField(max_length=200)

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
        """Check all order items against Inventory in a single set of queries."""
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
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('order', 'variant')
        indexes = [
            models.Index(fields=['order', 'variant']),  # Explicit for query planner
            models.Index(fields=['variant']),  # Variant lookups
        ]

    def __str__(self):
        return f"{self.quantity} × {self.variant.sku}"
```

**File:** `homepointBackend/users/models.py` (if not present, similar pattern)

```python
class User(AbstractUser):
    # ... existing fields
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),  # Email login
            models.Index(fields=['username']),  # Username login
            models.Index(fields=['is_staff', 'is_active']),  # Staff queries
        ]
```

### Migration Steps

```bash
# Generate migrations (don't create them manually; let Django do it)
cd homepointBackend
python manage.py makemigrations

# Review the generated migration file (e.g., 0005_auto_add_indexes.py)
# Check that it only adds indexes, no data changes

# Test locally
python manage.py migrate

# In production, apply with appropriate timeout settings
# For PostgreSQL:
# SET maintenance_work_mem TO 1GB;  # Allocate more RAM for index creation
```

### Testing

```bash
# Check index creation:
psql -U $DB_USER -d $DB_NAME -c "\d products_product"
# Look for "Indexes:" section showing new indexes

# Verify query performance improvement:
cd homepointBackend
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> from products.models import Product
>>> with CaptureQueriesContext(connection) as context:
...     products = list(Product.objects.filter(is_active=True, category_id=1))
>>> print(f"Queries: {len(context)}, SQL: {[q['sql'] for q in context]}")
```

**Expected Impact:** 50-70% faster queries on indexed columns

---

## 1.2 Fix Select/Prefetch Issues in ViewSets

### Problem Analysis

**File:** `homepointBackend/orders/views.py` (Line 11)
```python
queryset = Order.objects.all().select_related('items__variant')
# MISSING: user relationship
```

This causes **1 query per order** to fetch the user.

**File:** `homepointBackend/products/views/product_cat_views.py` (Lines 54-56)
```python
queryset = Product.objects.filter(is_active=True).prefetch_related(
    'variants__inventory'
)
# MISSING: product images for gallery
```

### Solutions

**File:** `homepointBackend/orders/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F, Prefetch
from .models import Order, OrderItem
from .serializers import OrderCreateSerializer, OrderDetailSerializer

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # Define default queryset with all necessary prefetches
    def get_queryset(self):
        queryset = Order.objects.select_related(
            'user'  # ← ADD: User relationship
        ).prefetch_related(
            'items__variant__product',  # ← ADD: Access product.name in serializer
            'items__variant__inventory'  # ← ADD: Stock data
        )
        
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer

    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data.pop('items')
        phone_number = serializer.validated_data['phone_number']

        # Lock relevant inventory rows
        from products.models import Inventory
        variant_ids = [item['variant'].id for item in items_data]
        inventories = Inventory.objects.select_for_update().filter(variant_id__in=variant_ids)

        # Build stock map
        stock_map = {inv.variant_id: inv.quantity for inv in inventories}
        insufficient = []

        total_amount = 0
        order_items_to_create = []

        for item in items_data:
            variant = item['variant']
            qty = item['quantity']
            available = stock_map.get(variant.id, 0)

            if available < qty:
                insufficient.append(f"{variant.sku}: requested {qty}, available {available}")
                continue

            total_amount += variant.price * qty
            order_items_to_create.append(OrderItem(
                variant=variant,
                quantity=qty,
                price_at_purchase=variant.price
            ))

        if insufficient:
            return Response({
                "detail": "Insufficient stock for some items",
                "errors": insufficient
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            phone_number=phone_number,
            delivery_location=serializer.validated_data['delivery_location'],
            total_amount=total_amount,
            status='pending'
        )

        # Bulk create items
        for item in order_items_to_create:
            item.order = order
        OrderItem.objects.bulk_create(order_items_to_create)

        # Atomically deduct stock using F expressions
        for item in order_items_to_create:
            Inventory.objects.filter(variant=item.variant).update(
                quantity=F('quantity') - item.quantity
            )

        # Serialize response with proper prefetches
        order_with_prefetches = self.get_queryset().get(pk=order.pk)
        response_serializer = OrderDetailSerializer(order_with_prefetches)
        return Response({
            "message": "Order created successfully. Proceed to M-Pesa payment.",
            "order": response_serializer.data
        }, status=status.HTTP_201_CREATED)
```

**File:** `homepointBackend/products/views/product_cat_views.py`

```python
from django.db.models import Q, Prefetch
from rest_framework import viewsets, filters, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from ..permissions import IsWarehouseStaff
from ..models import Category, Product, Variant, Inventory, StockMovement, ProductImage, VariantImage
from ..serializers import (
    CategorySerializer, ProductSerializer,
    VariantSerializer, InventorySerializer, get_user_role
)

class BaseProductViewSet(viewsets.GenericViewSet):
    """Base ViewSet for products that handles permissions and context logic."""
    
    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [(IsAdminUser | IsWarehouseStaff)()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['role'] = get_user_role(self.request)
        return context


class FullCRUDViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      BaseProductViewSet):
    """Generic ViewSet that provides standard CRUD actions."""
    pass


class CategoryViewSet(FullCRUDViewSet):
    queryset = Category.objects.all().prefetch_related(
        'products__variants__inventory',
        'products__images'  # ← ADD: Product images
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ProductViewSet(FullCRUDViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['base_price']

    def get_queryset(self):
        # Use Prefetch to conditionally load images
        variant_prefetch = Prefetch(
            'variants',
            Variant.objects.prefetch_related(
                'inventory',
                'images'  # ← ADD: Variant images
            )
        )
        
        queryset = Product.objects.filter(is_active=True).prefetch_related(
            variant_prefetch,
            'images'  # ← ADD: Product images
        ).select_related('category')

        category_id = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class VariantViewSet(FullCRUDViewSet):
    serializer_class = VariantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['sku', 'attributes']

    def get_queryset(self):
        return Variant.objects.select_related(
            'product'
        ).prefetch_related(
            'inventory',
            'images'  # ← ADD: Variant images
        )


class InventoryViewSet(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       BaseProductViewSet):
    """Simple endpoint for stock checks and admin updates."""
    serializer_class = InventorySerializer

    def retrieve(self, request, pk=None):
        variant = get_object_or_404(Variant.objects.select_related('inventory'), pk=pk)
        serializer = InventorySerializer(variant.inventory)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """Custom partial update logic for inventory movement."""
        variant = get_object_or_404(Variant.objects.select_related('inventory'), pk=pk)
        inventory = variant.inventory
        serializer = InventorySerializer(inventory, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            with transaction.atomic():
                change = serializer.validated_data['change_amount']
                m_type = serializer.validated_data['movement_type']

                if m_type == "IN":
                    inventory.quantity = F('quantity') + change
                else:
                    inventory.quantity = F('quantity') - change
                
                inventory.save()
                
                StockMovement.objects.create(
                    inventory=inventory,
                    variant=variant,
                    user=request.user,
                    change_amount=change,
                    movement_type=m_type,
                    reason=request.data.get('reason', '')
                )

                inventory.refresh_from_db()

            serializer = InventorySerializer(inventory)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Testing Query Count

```python
# Test file: homepointBackend/test_query_optimization.py
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from products.models import Product, Category, Variant, Inventory
from orders.models import Order, OrderItem

class QueryOptimizationTests(TestCase):
    def setUp(self):
        """Create test data."""
        cat = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            category=cat,
            description="Test",
            base_price=100.00
        )
        self.variant = Variant.objects.create(
            product=self.product,
            sku="TEST-001",
            price=100.00
        )
        Inventory.objects.create(variant=self.variant, quantity=10)

    def test_product_list_queries(self):
        """Verify ProductViewSet list doesn't cause N+1."""
        from rest_framework.test import APIRequestFactory
        from products.views.product_cat_views import ProductViewSet

        factory = APIRequestFactory()
        request = factory.get('/products/')
        view = ProductViewSet.as_view({'get': 'list'})

        with CaptureQueriesContext(connection) as context:
            response = view(request)

        # Should be ~2-3 queries max (products, variants, images, inventory)
        print(f"Product list queries: {len(context)}")
        assert len(context) < 5, f"Too many queries: {len(context)}"

    def test_order_list_queries(self):
        """Verify OrderViewSet list doesn't cause N+1."""
        from rest_framework.test import APIRequestFactory
        from orders.views import OrderViewSet
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(username='test', email='test@test.com')
        order = Order.objects.create(
            user=user,
            phone_number='0700000000',
            delivery_location='Nairobi',
            total_amount=100.00
        )
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            quantity=1,
            price_at_purchase=100.00
        )

        factory = APIRequestFactory()
        request = factory.get('/orders/')
        request.user = user
        view = OrderViewSet.as_view({'get': 'list'})

        with CaptureQueriesContext(connection) as context:
            response = view(request)

        print(f"Order list queries: {len(context)}")
        assert len(context) < 5, f"Too many queries: {len(context)}"
```

**Run tests:**
```bash
cd homepointBackend
python manage.py test test_query_optimization.QueryOptimizationTests --verbosity=2
```

**Expected Impact:** 60-80% reduction in queries per request

---

# PHASE 2: Caching Layer (Week 2)

## 2.1 Configure Redis Cache

**Why:** Products and categories change infrequently; cache them for 300 seconds (5 min).

### Setup Redis

**File:** `homepointBackend/requirements.txt` (add if not present)
```
redis==7.4.0
django-redis==5.4.0
```

### Configuration

**File:** `homepointBackend/homepointBackend/settings.py`

```python
import os
from decouple import config

# ========== CACHING CONFIGURATION ==========
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Graceful fallback if Redis down
        },
        'KEY_PREFIX': 'homepoint',
        'TIMEOUT': 300,  # Default 5-minute TTL
    }
}

# Session backend (optional, for sticky sessions)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Docker Compose Update

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:17-alpine
    container_name: homepoint-db
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d 
    env_file:
      - .env
    ports:
      - "5433:${DB_PORT}"
    networks:
      - homepoint_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: homepoint-redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - homepoint_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Django Backend API
  backend:
    build:
      context: ./homepointBackend
      dockerfile: Dockerfile
    container_name: homepoint-backend
    env_file:
      - .env
    environment:
      REDIS_URL: redis://redis:6379/1
    volumes:
      - ./homepointBackend:/app
      - static_volume:/app/staticfiles_collected
    ports:
      - "8000:8000"
    networks:
      - homepoint_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    command: >
      sh -c "
        python manage.py wait_for_db &&
        python manage.py migrate &&
        python manage.py collectstatic --noinput &&
        gunicorn homepointBackend.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
      "

  # Celery Worker
  celery:
    build:
      context: ./homepointBackend
      dockerfile: Dockerfile
    container_name: homepoint-celery
    command: celery -A homepointBackend worker -l info --concurrency=4
    env_file:
      - .env
    environment:
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    volumes:
      - ./homepointBackend:/app
    networks:
      - homepoint_network
    depends_on:
      - redis
      - db
    restart: unless-stopped

  # Celery Beat (for scheduled tasks)
  celery-beat:
    build:
      context: ./homepointBackend
      dockerfile: Dockerfile
    container_name: homepoint-celery-beat
    command: celery -A homepointBackend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file:
      - .env
    environment:
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    volumes:
      - ./homepointBackend:/app
    networks:
      - homepoint_network
    depends_on:
      - redis
      - db
    restart: unless-stopped

  # Vue.js Frontend
  frontend:
    build:
      context: ./homepointFrontend
      dockerfile: Dockerfile
    container_name: homepoint-frontend
    environment:
      VITE_API_BASE_URL: ${VITE_API_BASE_URL:-http://localhost:8000}
      VITE_STORE_NAME: ${VITE_STORE_NAME:-Homepoint POS}
      NODE_ENV: ${NODE_ENV:-production}
    ports:
      - "5173:8080"
    networks:
      - homepoint_network
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: homepoint-nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - homepoint_network
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  static_volume:
    driver: local

networks:
  homepoint_network:
    driver: bridge
```

## 2.2 Implement Cache on Hot Endpoints

**File:** `homepointBackend/products/views/product_cat_views.py`

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.response import Response

class CategoryViewSet(FullCRUDViewSet):
    queryset = Category.objects.all().prefetch_related(
        'products__variants__inventory',
        'products__images'
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def list(self, request, *args, **kwargs):
        """Cache category list for 5 minutes."""
        cache_key = f'categories:list:{request.query_params.urlencode()}'
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)  # 5 minutes
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual category for 10 minutes."""
        slug = kwargs.get('slug')
        cache_key = f'category:detail:{slug}'
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, 600)  # 10 minutes
        return response

    def perform_create(self, serializer):
        """Invalidate cache on create."""
        result = super().perform_create(serializer)
        cache.delete_pattern('categories:*')
        return result

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        result = super().perform_update(serializer)
        cache.delete_pattern('categories:*')
        cache.delete(f'category:detail:{self.get_object().slug}')
        return result

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        super().perform_destroy(instance)
        cache.delete_pattern('categories:*')


class ProductViewSet(FullCRUDViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['base_price']

    def get_queryset(self):
        variant_prefetch = Prefetch(
            'variants',
            Variant.objects.prefetch_related('inventory', 'images')
        )
        queryset = Product.objects.filter(is_active=True).prefetch_related(
            variant_prefetch, 'images'
        ).select_related('category')
        
        category_id = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset

    def list(self, request, *args, **kwargs):
        """Cache product list for 5 minutes."""
        cache_key = f'products:list:{request.query_params.urlencode()}'
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache individual product for 10 minutes."""
        slug = kwargs.get('slug')
        cache_key = f'product:detail:{slug}'
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return Response(cached_response)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, 600)
        return response

    def perform_create(self, serializer):
        """Invalidate cache on create."""
        result = super().perform_create(serializer)
        cache.delete_pattern('products:*')
        return result

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        result = super().perform_update(serializer)
        cache.delete_pattern('products:*')
        cache.delete(f'product:detail:{self.get_object().slug}')
        # Also invalidate category cache
        cache.delete_pattern('categories:*')
        return result

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        super().perform_destroy(instance)
        cache.delete_pattern('products:*')
        cache.delete_pattern('categories:*')


class VariantViewSet(FullCRUDViewSet):
    serializer_class = VariantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['sku', 'attributes']

    def get_queryset(self):
        return Variant.objects.select_related(
            'product'
        ).prefetch_related('inventory', 'images')

    def list(self, request, *args, **kwargs):
        """Cache variant list for 5 minutes."""
        cache_key = f'variants:list:{request.query_params.urlencode()}'
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)
        return response

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        result = super().perform_update(serializer)
        cache.delete_pattern('variants:*')
        cache.delete_pattern('products:*')
        return result

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        super().perform_destroy(instance)
        cache.delete_pattern('variants:*')
        cache.delete_pattern('products:*')
```

## 2.3 Cache Key Management Utility

**File:** `homepointBackend/products/cache_keys.py` (new)

```python
"""Cache key management for products app."""

def get_categories_list_key(params):
    """Generate cache key for categories list."""
    return f'categories:list:{params.urlencode() if params else "all"}'

def get_category_detail_key(slug):
    """Generate cache key for category detail."""
    return f'category:detail:{slug}'

def get_products_list_key(params):
    """Generate cache key for products list."""
    return f'products:list:{params.urlencode() if params else "all"}'

def get_product_detail_key(slug):
    """Generate cache key for product detail."""
    return f'product:detail:{slug}'

def get_variants_list_key(params):
    """Generate cache key for variants list."""
    return f'variants:list:{params.urlencode() if params else "all"}'

def get_inventory_key(variant_id):
    """Generate cache key for inventory data."""
    return f'inventory:variant:{variant_id}'

def invalidate_category_cache():
    """Invalidate all category-related caches."""
    from django.core.cache import cache
    cache.delete_pattern('categories:*')
    cache.delete_pattern('products:*')  # Products depend on categories

def invalidate_product_cache():
    """Invalidate all product-related caches."""
    from django.core.cache import cache
    cache.delete_pattern('products:*')

def invalidate_variant_cache():
    """Invalidate all variant-related caches."""
    from django.core.cache import cache
    cache.delete_pattern('variants:*')
    cache.delete_pattern('inventory:*')

def invalidate_inventory_cache(variant_id=None):
    """Invalidate inventory cache for variant."""
    from django.core.cache import cache
    if variant_id:
        cache.delete(get_inventory_key(variant_id))
    else:
        cache.delete_pattern('inventory:*')
```

### Testing Cache Effectiveness

**File:** `homepointBackend/test_caching.py`

```python
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIRequestFactory
from products.models import Product, Category, Variant, Inventory
from products.views.product_cat_views import ProductViewSet

@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
})
class CachingTests(TestCase):
    def setUp(self):
        cache.clear()
        cat = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            category=cat,
            description="Test",
            base_price=100.00
        )
        self.variant = Variant.objects.create(
            product=self.product,
            sku="TEST-001",
            price=100.00
        )
        Inventory.objects.create(variant=self.variant, quantity=10)

    def test_product_list_caching(self):
        """Verify product list is cached after first request."""
        factory = APIRequestFactory()
        request = factory.get('/products/')
        view = ProductViewSet.as_view({'get': 'list'})

        # First request (should query DB)
        with CaptureQueriesContext(connection) as context1:
            response1 = view(request)
        queries_first = len(context1)

        # Second request (should use cache, no DB queries)
        with CaptureQueriesContext(connection) as context2:
            response2 = view(request)
        queries_second = len(context2)

        print(f"First request queries: {queries_first}, Second request queries: {queries_second}")
        assert queries_second == 0, "Second request should not hit database (should use cache)"
        assert response1.data == response2.data, "Cached response should be identical"
```

**Run tests:**
```bash
python manage.py test test_caching.CachingTests --verbosity=2
```

**Expected Impact:** 90% reduction in queries for repeated requests, <10ms response times

---

# PHASE 3: Async Task Processing (Week 3)

## 3.1 Configure Celery

**File:** `homepointBackend/homepointBackend/settings.py`

```python
# ========== CELERY CONFIGURATION ==========
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'
CELERY_ENABLE_UTC = True

CELERY_TASK_DEFAULT_RETRY_DELAY = 60
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_TIME_LIMIT = 30 * 60  # 30 minutes

# Task routing for priority queues
CELERY_TASK_ROUTES = {
    'products.tasks.process_image_optimization_task': {'queue': 'images'},
    'orders.tasks.send_payment_confirmation': {'queue': 'payments'},
    'users.tasks.send_welcome_email': {'queue': 'emails'},
}

# Task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # Hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # Soft limit (give time to cleanup)
```

## 3.2 Expand Celery Tasks

**File:** `homepointBackend/products/tasks.py`

```python
import boto3
from celery import shared_task
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError
import requests
from django.core.cache import cache
from .models import ProductImage, VariantImage

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(requests.RequestException, BotoCoreError, ClientError),
    retry_backoff=True
)
def process_image_optimization_task(self, image_id, model_type='product'):
    """Optimize and upload image to S3. Non-blocking."""
    if model_type == "product":
        model_class = ProductImage
    elif model_type == "variant":
        model_class = VariantImage
    else:
        return "Unsupported model path variant."

    try:
        obj = model_class.objects.get(pk=image_id)
    except model_class.DoesNotExist:
        return f"Image record {image_id} went missing."

    # Idempotency lock
    if obj.optimization_status == 'done' and obj.optimized_url:
        return f"Object {image_id} processing skip lock caught."

    # Mark as processing
    obj.optimization_status = 'processing'
    obj.save(update_fields=['optimization_status'])

    try:
        # Download and optimize
        from .utils.image import optimize_and_resize_external_image
        optimized_io = optimize_and_resize_external_image(
            external_url=obj.raw_external_url,
            max_width=800,
            quality=78
        )

        # Upload to S3
        from django.conf import settings
        from botocore.config import Config
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        target_s3_key = obj.get_s3_key()
        
        s3_client.upload_fileobj(
            Fileobj=optimized_io,
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=target_s3_key,
            ExtraArgs={
                'ContentType': 'image/webp',
                'CacheControl': 'max-age=31536000, public'
            }
        )

        # Save locally
        from django.core.files.base import ContentFile
        filename = target_s3_key.split('/')[-1]
        optimized_io.seek(0)
        obj.local_image.save(filename, ContentFile(optimized_io.read()), save=False)

        # Mark as done
        domain = settings.CLOUDFRONT_DOMAIN or f"{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
        obj.optimized_url = f"https://{domain}/{target_s3_key}"
        obj.optimization_status = 'done'
        obj.last_optimized_at = timezone.now()
        obj.error_log = None
        obj.save(update_fields=['optimized_url', 'local_image', 'optimization_status', 'last_optimized_at', 'error_log'])
        
        # Invalidate product/variant cache
        if model_type == 'product':
            cache.delete_pattern('products:*')
        else:
            cache.delete_pattern('variants:*')
        
        return f"Successfully optimized image ID: {image_id}"

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            obj.optimization_status = 'failed'
            obj.error_log = str(exc)
            obj.save(update_fields=['optimization_status', 'error_log'])
        
        raise exc


@shared_task(bind=True, max_retries=3)
def update_low_stock_alerts(self):
    """Run periodically to flag low-stock items."""
    from .models import Inventory
    from django.core.mail import send_mass_mail
    
    try:
        low_stock_items = Inventory.objects.filter(
            quantity__lte=models.F('variant__stock_threshold')
        ).select_related('variant__product')

        if not low_stock_items.exists():
            return "No low stock items found."

        # Log low stock items
        for item in low_stock_items:
            print(f"LOW STOCK: {item.variant.sku} - {item.quantity} units")

        return f"Checked {low_stock_items.count()} low stock items."

    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@shared_task
def cleanup_expired_images():
    """Run daily to clean up orphaned image records."""
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete images not yet processed after 24 hours
    cutoff = timezone.now() - timedelta(hours=24)
    
    expired_product_images = ProductImage.objects.filter(
        created_at__lt=cutoff,
        optimization_status='pending'
    )
    expired_variant_images = VariantImage.objects.filter(
        created_at__lt=cutoff,
        optimization_status='pending'
    )
    
    count_product = expired_product_images.count()
    count_variant = expired_variant_images.count()
    
    expired_product_images.delete()
    expired_variant_images.delete()
    
    return f"Cleaned up {count_product + count_variant} expired images."
```

**File:** `homepointBackend/orders/tasks.py` (new)

```python
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import requests

@shared_task(bind=True, max_retries=3)
def send_payment_confirmation(self, order_id):
    """Send payment confirmation email/SMS."""
    from .models import Order
    
    try:
        order = Order.objects.select_related('user').get(pk=order_id)
        
        # Send email
        if order.user and order.user.email:
            send_mail(
                subject=f'Order #{order.id} - Payment Confirmation',
                message=f'Your order has been received. Proceed to M-Pesa payment.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
        
        # Send SMS (if service configured)
        if settings.TWILIO_ENABLED:
            send_sms_notification(order.phone_number, f'Order {order.id} received. Total: KES {order.total_amount}')
        
        return f"Confirmation sent for order {order_id}"
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2)
def send_sms_notification(self, phone_number, message):
    """Send SMS via Twilio or local SMS service."""
    try:
        # Replace with your SMS service
        response = requests.post(
            'https://api.example.com/sms',
            json={
                'phone': phone_number,
                'message': message,
            },
            timeout=10
        )
        response.raise_for_status()
        return f"SMS sent to {phone_number}"
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@shared_task
def generate_daily_sales_report():
    """Generate and cache daily sales report."""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum
    from .models import Order
    
    today = timezone.now().date()
    orders = Order.objects.filter(
        created_at__date=today,
        status='paid'
    )
    
    total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    order_count = orders.count()
    
    # Cache report
    from django.core.cache import cache
    cache.set(f'report:daily:{today}', {
        'date': today,
        'total_sales': total_sales,
        'order_count': order_count,
    }, 86400)  # 24 hours
    
    return f"Daily report generated: {order_count} orders, KES {total_sales}"
```

**File:** `homepointBackend/users/tasks.py` (new)

```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task(bind=True, max_retries=2)
def send_welcome_email(self, user_id):
    """Send welcome email to new users."""
    from .models import User
    
    try:
        user = User.objects.get(pk=user_id)
        
        if not user.email:
            return f"User {user_id} has no email."
        
        send_mail(
            subject='Welcome to Homepoint!',
            message=f'Hello {user.get_full_name()},\n\nWelcome to Homepoint POS.',
            from_email='noreply@homepoint.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return f"Welcome email sent to {user.email}"
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

## 3.3 Integrate Tasks into Views

**File:** `homepointBackend/products/views/image_pipeline_views.py` (update)

```python
# ... existing code ...

class InventoryUploadFinalizeView(UploadPipelineMixin, APIView):
    """Step 2: Client successfully pushed raw bytes to S3."""
    
    def post(self, request):
        uploaded_keys = request.data.get('keys', [])
        model_type, target_id, ImageModel, fk_field = self.resolve_target_context(request.data)

        if not target_id or not uploaded_keys:
            return Response({"error": "Missing target_id or keys list"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not model_type:
            return Response({"error": "Invalid model_type"}, status=status.HTTP_400_BAD_REQUEST)

        created_task_ids = []
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        region = settings.AWS_S3_REGION_NAME

        for key in uploaded_keys:
            raw_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
            
            create_kwargs = {
                fk_field: target_id,
                'raw_external_url': raw_url,
                'optimization_status': 'pending'
            }
            img_obj = ImageModel.objects.create(**create_kwargs)
            
            # IMMEDIATELY queue task (non-blocking)
            from ..tasks import process_image_optimization_task
            task = process_image_optimization_task.delay(img_obj.id, model_type=model_type)
            created_task_ids.append({
                'image_id': img_obj.id,
                'task_id': task.id,
                'status': 'pending'
            })

        return Response({
            "message": f"{model_type.capitalize()} images queued for processing.",
            "tasks": created_task_ids
        }, status=status.HTTP_202_ACCEPTED)


class ImageProcessingStatusView(APIView):
    """Poll task status."""
    
    def get(self, request, task_id):
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        return Response({
            'task_id': task_id,
            'status': task.status,
            'result': task.result if task.successful() else None,
        })
```

**File:** `homepointBackend/orders/views.py` (update)

```python
# Add to OrderViewSet.create()

@transaction.atomic
def create(self, request):
    # ... existing code ...
    
    # After order creation:
    order = Order.objects.create(...)
    
    # Queue confirmation email (non-blocking)
    from ..tasks import send_payment_confirmation
    send_payment_confirmation.delay(order.id)
    
    # Serialize response
    response_serializer = OrderDetailSerializer(order)
    return Response({
        "message": "Order created successfully. Proceed to M-Pesa payment.",
        "order": response_serializer.data
    }, status=status.HTTP_201_CREATED)
```

---

# PHASE 4: Response Size & Serialization (Week 3)

## 4.1 Optimize Serializers

**Problem:** Returning all fields for customers who only need status, not raw stock numbers.

**File:** `homepointBackend/products/serializers.py` (update)

```python
from rest_framework import serializers
from .models import Category, Product, Variant, Inventory, StockMovement, VariantImage, ProductImage

def get_user_role(request):
    """Read role directly from user."""
    if request is None:
        return 'customer'
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return 'customer'
    return getattr(user, 'role', 'customer')


PRIVILEGED_ROLES = {'admin', 'staff'}


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent']


class ProductImageSerializerMinimal(serializers.ModelSerializer):
    """Minimal image serializer for list endpoints."""
    class Meta:
        model = ProductImage
        fields = ['id', 'optimized_url']  # Only essential fields


class ProductImageSerializerFull(serializers.ModelSerializer):
    """Full image serializer for detail endpoints."""
    class Meta:
        model = ProductImage
        fields = ['id', 'raw_external_url', 'optimized_url', 'optimization_status', 'local_image']


class VariantImageSerializerMinimal(serializers.ModelSerializer):
    """Minimal variant image."""
    class Meta:
        model = VariantImage
        fields = ['id', 'optimized_url']


class InventorySerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()
    change_amount = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    movement_type = serializers.ChoiceField(choices=StockMovement.MOVEMENT_TYPES, write_only=True)
    reason = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Inventory
        fields = ['quantity', 'is_low_stock', 'last_updated', 'change_amount', 'movement_type', 'reason']
        read_only_fields = ['quantity', 'is_low_stock', 'last_updated']


class VariantSerializerMinimal(serializers.ModelSerializer):
    """Minimal variant for product listings."""
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Variant
        fields = ['id', 'sku', 'price', 'unit_type', 'unit_type_display', 'stock_status']

    def get_stock_status(self, obj):
        inv = getattr(obj, 'inventory', None)
        qty = getattr(inv, 'quantity', 0) or 0
        threshold = obj.stock_threshold or 10
        if qty <= 0:
            return 'out_of_stock'
        if qty <= threshold:
            return 'low_stock'
        return 'in_stock'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        role = self.context.get('role', 'customer')
        
        # Customers don't see stock status
        if role == 'customer':
            data.pop('stock_status', None)
        
        return data


class VariantSerializerFull(serializers.ModelSerializer):
    """Full variant with all details."""
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    images = VariantImageSerializerMinimal(many=True, required=False)
    stock_quantity = serializers.SerializerMethodField()
    stock_threshold = serializers.SerializerMethodField()
    stock_last_updated = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Variant
        fields = [
            'id', 'sku', 'item_code', 'attributes', 'price', 'unit_type',
            'unit_type_display', 'tax_type', 'stock_quantity', 'stock_threshold',
            'stock_last_updated', 'stock_status', 'images'
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variant = Variant.objects.create(**validated_data)
        for image_data in images_data:
            VariantImage.objects.create(variant=variant, **image_data)
        return variant

    def get_stock_quantity(self, obj):
        inv = getattr(obj, 'inventory', None)
        return getattr(inv, 'quantity', 0)

    def get_stock_threshold(self, obj):
        return obj.stock_threshold

    def get_stock_last_updated(self, obj):
        inv = getattr(obj, 'inventory', None)
        return getattr(inv, 'last_updated', None)

    def get_stock_status(self, obj):
        inv = getattr(obj, 'inventory', None)
        qty = getattr(inv, 'quantity', 0) or 0
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
            data.pop('stock_quantity', None)
            data.pop('stock_threshold', None)
            data.pop('stock_last_updated', None)

        if role == 'customer':
            data.pop('stock_status', None)

        return data


class ProductSerializerMinimal(serializers.ModelSerializer):
    """Minimal product for listings."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageSerializerMinimal(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'base_price', 'category_name', 'images']


class ProductSerializerFull(serializers.ModelSerializer):
    """Full product with all details."""
    category_detail = CategorySerializer(source='category', read_only=True)
    variants = VariantSerializerFull(many=True, read_only=True)
    images = ProductImageSerializerFull(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'base_price',
            'is_active', 'category', 'category_detail', 'variants', 'images'
        ]


# Use in views:
class ProductViewSet(FullCRUDViewSet):
    serializer_class = ProductSerializerMinimal  # Default
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductSerializerMinimal  # Lightweight for lists
        return ProductSerializerFull  # Full details for retrieve
```

---

# PHASE 5: Monitoring & Profiling (Week 4)

## 5.1 Django Silk Integration

**File:** `homepointBackend/homepointBackend/urls.py`

```python
# Already configured in settings, just ensure paths work
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

from django.http import HttpResponse
def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('health/', health_check),
    path('admin/', admin.site.urls),
    path('silk/', include('silk.urls', namespace='silk')),  # ← Django Silk
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Access:** `http://localhost:8000/silk/` to see request profiles

## 5.2 Query Analysis Script

**File:** `homepointBackend/scripts/analyze_queries.py` (new)

```python
"""Analyze and profile database queries."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homepointBackend.settings')
django.setup()

from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIRequestFactory
from products.views.product_cat_views import ProductViewSet, CategoryViewSet
from orders.views import OrderViewSet

def analyze_endpoint(viewset_class, action, request_data=None):
    """Analyze query count and execution time for an endpoint."""
    factory = APIRequestFactory()
    
    if action == 'list':
        request = factory.get('/endpoint/')
    elif action == 'retrieve':
        request = factory.get('/endpoint/1/')
    elif action == 'create':
        request = factory.post('/endpoint/', request_data or {})
    
    view = viewset_class.as_view({request.method.lower(): action})
    
    with CaptureQueriesContext(connection) as context:
        response = view(request)
    
    queries = context
    print(f"\n{'='*60}")
    print(f"{viewset_class.__name__}.{action}")
    print(f"{'='*60}")
    print(f"Total queries: {len(queries)}")
    print(f"Response time: ~{sum(q['time'] for q in queries):.3f}s")
    
    # Group by table
    table_counts = {}
    for q in queries:
        table = q['sql'].split('FROM')[1].split()[0] if 'FROM' in q['sql'] else 'Unknown'
        table_counts[table] = table_counts.get(table, 0) + 1
    
    print(f"\nQueries by table:")
    for table, count in sorted(table_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {table}: {count}")
    
    print(f"\nSlowest queries:")
    sorted_queries = sorted(queries, key=lambda q: q['time'], reverse=True)[:3]
    for i, q in enumerate(sorted_queries, 1):
        print(f"  {i}. {q['time']:.3f}s - {q['sql'][:80]}...")

if __name__ == '__main__':
    print("Analyzing common endpoints...\n")
    
    analyze_endpoint(ProductViewSet, 'list')
    analyze_endpoint(CategoryViewSet, 'list')
    analyze_endpoint(OrderViewSet, 'list')
```

**Run:** `python scripts/analyze_queries.py`

---

# PHASE 6: Load Testing & Deployment (Week 5-6)

## 6.1 Load Testing with Locust

**File:** `homepointBackend/locustfile.py`

```python
from locust import HttpUser, task, between
import random

class HomepointUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def browse_products(self):
        self.client.get("/products/", name="/products/")

    @task(2)
    def view_product_detail(self):
        product_id = random.randint(1, 100)
        self.client.get(f"/products/{product_id}/", name="/products/[id]/")

    @task(1)
    def create_order(self):
        order_data = {
            "phone_number": "0700000000",
            "delivery_location": "Nairobi",
            "items": [{"variant_id": 1, "quantity": 2}]
        }
        self.client.post("/orders/", json=order_data, name="/orders/ CREATE")
```

**Run test:**
```bash
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

## 6.2 Performance Checklist

```markdown
### Pre-Deployment Checklist

- [ ] All database indexes created and tested
- [ ] Redis cache configured and running
- [ ] Celery workers running (check docker-compose)
- [ ] Serializers optimized for role-based responses
- [ ] Query counts verified (< 5 per endpoint)
- [ ] Cache invalidation logic working
- [ ] Load test passed (100 users, < 2s p95 latency)
- [ ] Django Silk profiles reviewed
- [ ] Error handling for cache misses
- [ ] Celery task monitoring (Flower)
- [ ] Database connection pooling configured
- [ ] CloudFront/CDN configured for images
- [ ] Monitoring alerts configured

### Monitoring Commands

```bash
# Monitor Celery tasks
celery -A homepointBackend events

# Check Redis memory
redis-cli INFO memory

# Monitor PostgreSQL connections
psql -U $DB_USER -d $DB_NAME -c "SELECT datname, usename, count(*) FROM pg_stat_activity GROUP BY datname, usename;"

# Check Django Silk
curl http://localhost:8000/silk/
```
```

---

# Summary Table

| Phase | Component | Change | Impact | Timeline |
|-------|-----------|--------|--------|----------|
| 1 | Database | Add indexes | 50-70% faster queries | Day 1-2 |
| 1 | Queries | Fix N+1 (select_related) | 60-80% fewer queries | Day 2-3 |
| 2 | Cache | Redis + DRF cache_page | 90% faster list endpoints | Day 4-5 |
| 3 | Tasks | Celery for images/emails | Request time -50% | Day 6-7 |
| 4 | Serializers | Role-based fields | Response size -30% | Day 8 |
| 5 | Monitoring | Django Silk + analysis | Visibility into bottlenecks | Day 9 |
| 6 | Load test | Locust simulation | Confidence in scalability | Day 10 |

---

# Success Criteria

✅ **P95 latency:** < 500ms (currently ~1.5s)  
✅ **Throughput:** 1000+ req/s (currently ~100)  
✅ **Database queries:** < 5 per request (currently 15-20)  
✅ **Cache hit rate:** > 70% for product endpoints  
✅ **Celery task completion:** < 10s for image processing  

---

# Questions to Guide Implementation

1. **Which endpoints are slowest today?** (Use Django Silk to find out)
2. **How frequently do products/categories change?** (Determines cache TTL)
3. **What image sizes are you serving?** (Affects optimization task time)
4. **Do you have monitoring/alerting?** (For cache failures, Celery worker down)
5. **Can you handle order spike?** (Helps size Celery worker pool)

---

**Next Steps:**
1. Start with Phase 1 (indexes) — lowest risk, high impact
2. Verify each phase with load tests
3. Monitor production with Silk after each deployment
4. Adjust cache TTLs based on usage patterns
