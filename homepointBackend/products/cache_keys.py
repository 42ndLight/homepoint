"""Cache key management and invalidation for products app."""
import fnmatch
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

def get_categories_list_key(params):
    """Generate cache key for categories list."""
    return f'categories:list:{params.urlencode() if params else "all"}'

def get_category_detail_key(slug):
    """Generate cache key for category detail."""
    return f'category:detail:{slug}'

def get_products_list_key(params, role=None):
    """Generate cache key for products list, optionally including role for isolation."""
    base = f'products:list:{params.urlencode() if params else "all"}'
    if role:
        return f"{base}:role:{role}"
    return base

def get_product_detail_key(slug):
    """Generate cache key for product detail."""
    return f'product:detail:{slug}'

def get_variants_list_key(params):
    """Generate cache key for variants list."""
    return f'variants:list:{params.urlencode() if params else "all"}'

def get_inventory_key(variant_id):
    """Generate cache key for inventory data."""
    return f'inventory:variant:{variant_id}'

def safe_delete_pattern(pattern):
    """Delete keys matching pattern, with fallback for non-redis backends."""
    # django-redis cache backend supports delete_pattern directly
    if hasattr(cache, 'delete_pattern'):
        try:
            cache.delete_pattern(pattern)
            return
        except Exception as e:
            logger.error("Error using delete_pattern for %s: %s", pattern, e)
            
    # Fallback for LocMemCache (used in tests) or other backends
    if hasattr(cache, '_cache'):
        # LocMemCache stores its keys in cache._cache
        try:
            keys_to_delete = [
                key for key in cache._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            for key in keys_to_delete:
                cache.delete(key)
            return
        except Exception as e:
            logger.error("Error manually deleting keys matching %s: %s", pattern, e)
            
    # Last resort: log instead of clearing entire cache
    logger.warning("Could not safely delete cache pattern %s. Cache clear avoided.", pattern)

def invalidate_category_cache():
    """Invalidate all category-related caches."""
    safe_delete_pattern('*categories:*')
    safe_delete_pattern('*products:*')  # Products depend on categories

def invalidate_product_cache():
    """Invalidate all product-related caches."""
    safe_delete_pattern('*products:*')

def invalidate_variant_cache():
    """Invalidate all variant-related caches."""
    safe_delete_pattern('*variants:*')
    safe_delete_pattern('*inventory:*')

def invalidate_inventory_cache(variant_id=None):
    """Invalidate inventory cache for variant."""
    if variant_id:
        cache.delete(get_inventory_key(variant_id))
    else:
        safe_delete_pattern('*inventory:*')
