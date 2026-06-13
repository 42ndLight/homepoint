from django.urls import path
from rest_framework.routers import DefaultRouter
from products.views.product_cat_views import (
    CategoryViewSet, ProductViewSet,
    VariantViewSet, InventoryViewSet
)
from products.views.image_pipeline_views import(
    PresignedUrlGenerationView, 
    InventoryUploadFinalizeView
)

app_name='products'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', VariantViewSet, basename='variant')
router.register(r'inventory', InventoryViewSet, basename='inventory')


urlpatterns = [
    path('presignurl/', PresignedUrlGenerationView.as_view(), name='presignurl'),
    path('invupload/', InventoryUploadFinalizeView.as_view(), name='invupload')
] + router.urls