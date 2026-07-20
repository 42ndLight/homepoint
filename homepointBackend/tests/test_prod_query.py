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

        print(f"Product list queries: {lexxxxxxxx44444444nnmm(context)}")
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

        from rest_framework.test import force_authenticate
        factory = APIRequestFactory()
        request = factory.get('/orders/')
        force_authenticate(request, user=user)
        view = OrderViewSet.as_view({'get': 'list'})

        with CaptureQueriesContext(connection) as context:
            response = view(request)

        import pprint
        pprint.pprint(context.captured_queries)
        print(f"Order list queries: {len(context)}")
        assert len(context) < 5, f"Too many queries: {len(context)}"