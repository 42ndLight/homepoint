import json
import os
import time
import shutil
from django.core.management.base import BaseCommand
from products.models import Product, Variant, Category, Inventory

class Command(BaseCommand):
    help = 'Export full product, category, and inventory tree for frontend/offline use'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default='export_bundle',
            help='The output folder for the bundle',
        )

    def handle(self, *args, **kwargs):
        output_folder = kwargs['folder']
        
        # Ensure folder exists and is clean
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=True)

        self.stdout.write("Fetching categories...")
        # Get all categories and build a map for hierarchy
        all_categories = Category.objects.all()
        category_map = {cat.id: {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "parent_id": cat.parent_id,
            "subcategories": []
        } for cat in all_categories}
        
        category_tree = []
        for cat_id, cat_data in category_map.items():
            if cat_data["parent_id"]:
                parent = category_map.get(cat_data["parent_id"])
                if parent:
                    parent["subcategories"].append(cat_data)
                else:
                    # Parent not found in map (shouldn't happen with .all())
                    category_tree.append(cat_data)
            else:
                category_tree.append(cat_data)

        self.stdout.write(f"Bundling data from {Product.objects.count()} products...")

        export_data = []
        # Prefetch everything to avoid N+1 queries
        products = Product.objects.select_related('category').prefetch_related(
            'images',
            'variants__images',
            'variants__inventory'
        ).all()
        
        for product in products:
            product_entry = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "category": {
                    "id": product.category.id,
                    "name": product.category.name,
                    "slug": product.category.slug
                } if product.category else None,
                "base_price": float(product.base_price),
                "is_active": product.is_active,
                "product_images": [
                    {
                        "id": img.id,
                        "raw_url": img.raw_external_url,
                        "optimized_url": img.optimized_url,
                        "local_url": img.local_image.url if img.local_image else None,
                        "status": img.optimization_status
                    } for img in product.images.all()
                ],
                "variants": []
            }

            # Process Variants
            for variant in product.variants.all():
                # Inventory info (using 'inv' as requested)
                inv_data = {}
                try:
                    # Since it's a OneToOneField, it might not exist if not created
                    inv = variant.inventory
                    inv_data = {
                        "quantity": inv.quantity,
                        "location": inv.location,
                        "last_updated": inv.last_updated.isoformat() if inv.last_updated else None,
                        "is_low_stock": inv.is_low_stock()
                    }
                except Inventory.DoesNotExist:
                    inv_data = {
                        "quantity": 0,
                        "location": "",
                        "last_updated": None,
                        "is_low_stock": True
                    }

                variant_data = {
                    "id": variant.id,
                    "sku": variant.sku,
                    "price": float(variant.price),
                    "unit_type": variant.unit_type,
                    "attributes": variant.attributes,
                    "stock_threshold": variant.stock_threshold,
                    "item_code": variant.item_code,
                    "tax_type": variant.tax_type,
                    "inv": inv_data,
                    "variant_images": [
                        {
                            "id": img.id,
                            "raw_url": img.raw_external_url,
                            "optimized_url": img.optimized_url,
                            "local_url": img.local_image.url if img.local_image else None,
                            "status": img.optimization_status
                        } for img in variant.images.all()
                    ]
                }
                product_entry["variants"].append(variant_data)
            
            export_data.append(product_entry)

        # Build the final manifest
        manifest = {
            "categories": category_tree,
            "products": export_data,
            "metadata": {
                "timestamp": int(time.time()),
                "total_products": len(export_data),
                "total_categories": len(all_categories)
            }
        }

        # Save the JSON manifest
        manifest_path = os.path.join(output_folder, 'manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f'Successfully bundled {len(export_data)} products to {manifest_path}'))
