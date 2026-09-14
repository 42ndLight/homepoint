from django.urls import path
from rest_framework.routers import DefaultRouter
from products.views.image_pipeline_views import ImageUploadView
from products.views.product_control_views import ProductViewSet
from products.views.category_control_views import CategoryViewSet
from products.views.variant_control_views import VariantViewSet
from products.views.inventory_control_views import InventoryViewSet

app_name='products'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', VariantViewSet, basename='variant')
router.register(r'inventory', InventoryViewSet, basename='inventory')


urlpatterns = [
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
] + router.urls