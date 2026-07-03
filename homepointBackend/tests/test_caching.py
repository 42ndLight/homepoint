from django.test import TestCase, override_settings
from django.core.cache import cache
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate
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
