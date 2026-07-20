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
    from urllib.parse import urlencode

    # Define the parameters that actually affect the queryset/response
    allowed = {'page', 'page_size', 'category', 'search', 'ordering'}
    filtered = {k: params[k] for k in allowed if k in params}
    
    # Sort to ensure consistent keys regardless of query param order
    query_string = urlencode(sorted(filtered.items()))
    base = f'products:list:{query_string if query_string else "all"}'
    
    if role:
        return f"{base}:role:{role}"
    return base

def get_product_detail_key(slug, role=None):
    """Generate cache key for product detail."""
    base = f'product:detail:{slug}'
    if role:
        return f"{base}:role:{role}"
    return base

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
            keys_to_delete = list([
                key for key in cache._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ])
            for key in keys_to_delete:
                if key in cache._cache:
                    del cache._cache[key]
                if hasattr(cache, '_expire_info') and key in cache._expire_info:
                    del cache._expire_info[key]
            return
        except Exception as e:
            logger.exception("Error manually deleting keys matching %s: %s", pattern, e)
            
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
