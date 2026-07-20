from django.test import TestCase, override_settings
from django.core.cache import cache
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import Product, Category, Variant, Inventory
from products.views.product_cat_views import ProductViewSet

User = get_user_model()

@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
})
class CachingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='testuser', password='password123')
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
        force_authenticate(request, user=self.user)
        view = ProductViewSet.as_view({'get': 'list'})

        # First request (should query DB)
        with CaptureQueriesContext(connection) as context1:
            response1 = view(request)
        
        self.assertEqual(response1.status_code, 200, f"Expected 200 OK, got {response1.status_code} with data {response1.data}")
        queries_first = len(context1)
        self.assertGreater(queries_first, 0)

        # Second request (should use cache, no DB queries)
        request2 = factory.get('/products/')
        force_authenticate(request2, user=self.user)
        with CaptureQueriesContext(connection) as context2:
            response2 = view(request2)
        queries_second = len(context2)

        print(f"First request queries: {queries_first}, Second request queries: {queries_second}")
        self.assertEqual(queries_second, 0, "Second request should not hit database (should use cache)")
        self.assertEqual(response1.data, response2.data, "Cached response should be identical")

    def test_cache_invalidation_on_create(self):
        """Creating a product should clear the product list cache."""
        factory = APIRequestFactory()
        request = factory.get('/products/')
        force_authenticate(request, user=self.user)
        view = ProductViewSet.as_view({'get': 'list'})
        # Warm cache
        with CaptureQueriesContext(connection):
            view(request)
        # Create new product
        cat = Category.objects.get(name="Test Category")
        create_req = factory.post('/products/', {
            'name': 'New Product',
            'category': cat.id,
            'description': 'New',
            'base_price': 50.0,
        }, format='json')
        force_authenticate(create_req, user=self.user)
        create_view = ProductViewSet.as_view({'post': 'create'})
        create_resp = create_view(create_req)
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        # List again, should hit DB and include new product
        request2 = factory.get('/products/')
        force_authenticate(request2, user=self.user)
        with CaptureQueriesContext(connection) as ctx:
            resp2 = view(request2)
        self.assertGreater(len(ctx), 0)
        self.assertTrue(any(p['name'] == 'New Product' for p in resp2.data))

    def test_cache_invalidation_on_update(self):
        """Updating a product should clear the cached list."""
        factory = APIRequestFactory()
        # Warm cache
        req = factory.get('/products/')
        force_authenticate(req, user=self.user)
        view = ProductViewSet.as_view({'get': 'list'})
        with CaptureQueriesContext(connection):
            view(req)
        # Update product price
        update_req = factory.patch(f'/products/{self.product.slug}/', {'base_price': 200.0}, format='json')
        force_authenticate(update_req, user=self.user)
        update_view = ProductViewSet.as_view({'patch': 'partial_update'})
        update_resp = update_view(update_req, slug=self.product.slug)
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        # List again, should hit DB and reflect updated price
        req2 = factory.get('/products/')
        force_authenticate(req2, user=self.user)
        with CaptureQueriesContext(connection) as ctx:
            resp2 = view(req2)
        self.assertGreater(len(ctx), 0)
        updated = next(p for p in resp2.data if p['slug'] == self.product.slug)
        self.assertEqual(updated['base_price'], 200.0)

    def test_cache_invalidation_on_destroy(self):
        """Deleting a product should clear the cached list."""
        factory = APIRequestFactory()
        # Warm cache
        req = factory.get('/products/')
        force_authenticate(req, user=self.user)
        view = ProductViewSet.as_view({'get': 'list'})
        with CaptureQueriesContext(connection):
            view(req)
        # Delete product
        delete_req = factory.delete(f'/products/{self.product.slug}/')
        force_authenticate(delete_req, user=self.user)
        delete_view = ProductViewSet.as_view({'delete': 'destroy'})
        del_resp = delete_view(delete_req, slug=self.product.slug)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        # List again, should hit DB and not contain deleted product
        req2 = factory.get('/products/')
        force_authenticate(req2, user=self.user)
        with CaptureQueriesContext(connection) as ctx:
            resp2 = view(req2)
        self.assertGreater(len(ctx), 0)
        self.assertFalse(any(p['slug'] == self.product.slug for p in resp2.data))

    def test_cache_role_isolation(self):
        """Cache should be isolated per user role."""
        factory = APIRequestFactory()
        view = ProductViewSet.as_view({'get': 'list'})
        # First request as regular user (customer)
        req1 = factory.get('/products/')
        force_authenticate(req1, user=self.user)
        with CaptureQueriesContext(connection):
            resp1 = view(req1)
        # Create admin user
        admin_user = User.objects.create_user(username='adminuser', password='password123', role='admin')
        req2 = factory.get('/products/')
        force_authenticate(req2, user=admin_user)
        # Second request with admin role should hit DB (different cache key)
        with CaptureQueriesContext(connection) as ctx2:
            resp2 = view(req2)
        self.assertGreater(len(ctx2), 0)
        self.assertEqual(resp1.data, resp2.data)
        # Third request with same admin role should be cached (no DB queries)
        req3 = factory.get('/products/')
        force_authenticate(req3, user=admin_user)
        with CaptureQueriesContext(connection) as ctx3:
            resp3 = view(req3)
        self.assertEqual(len(ctx3), 0)
        self.assertEqual(resp2.data, resp3.data)
