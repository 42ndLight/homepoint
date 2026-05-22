import json
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db import transaction
from products.models import Category, Product, Variant, Inventory, ProductImage, VariantImage

class Command(BaseCommand):
    help = 'Seed products from manifest JSON'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to manifest JSON file')
        parser.add_argument('--keep-ids', action='store_true', help='Keep the IDs from the JSON file')

    def handle(self, *args, **options):
        file_path = options['file']
        keep_ids = options['keep_ids']
        
        if not file_path:
            # Search for latest manifest in homepointBackend/export_bundle
            bundle_dir = 'export_bundle'
            if not os.path.exists(bundle_dir):
                 bundle_dir = os.path.join('homepointBackend', 'export_bundle')
            
            if os.path.exists(bundle_dir):
                manifests = [f for f in os.listdir(bundle_dir) if f.startswith('manifest_') and f.endswith('.json')]
                if manifests:
                    manifests.sort()
                    file_path = os.path.join(bundle_dir, manifests[-1])
        
        if not file_path or not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Manifest file not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Seeding from {file_path}...'))
        
        base_dir = os.path.dirname(file_path)

        with open(file_path, 'r') as f:
            data = json.load(f)

        with transaction.atomic():
            for item in data:
                category_name = item.get('category', 'Uncategorized')
                category, _ = Category.objects.get_or_create(name=category_name)

                # Product data
                product_defaults = {
                    'name': item['name'],
                    'description': item['description'],
                    'category': category,
                    'base_price': item['base_price'],
                }
                
                if keep_ids:
                    product, created = Product.objects.update_or_create(
                        id=item['id'],
                        defaults=product_defaults
                    )
                else:
                    product, created = Product.objects.update_or_create(
                        slug=item['slug'],
                        defaults=product_defaults
                    )
                
                if created:
                    self.stdout.write(f"Created product: {product.name}")
                else:
                    self.stdout.write(f"Updated product: {product.name}")

                # Handle Product Images
                for img_rel_path in item.get('product_images', []):
                    img_full_path = os.path.join(base_dir, img_rel_path)
                    if os.path.exists(img_full_path):
                        with open(img_full_path, 'rb') as f:
                            django_file = File(f)
                            filename = os.path.basename(img_rel_path)
                            if not ProductImage.objects.filter(product=product, image__icontains=filename).exists():
                                pi = ProductImage(product=product)
                                pi.image.save(filename, django_file, save=True)

                # Handle Variants
                for v_data in item.get('variants', []):
                    variant_defaults = {
                        'product': product,
                        'price': v_data['price'],
                        'unit_type': v_data.get('unit_type', 'piece'),
                        'attributes': v_data.get('attributes', {}),
                        # Optional fields if they were in manifest, otherwise model defaults used
                        'item_code': v_data.get('item_code', ''),
                        'tax_type': v_data.get('tax_type', 'A'),
                    }
                    
                    if keep_ids:
                        variant, v_created = Variant.objects.update_or_create(
                            id=v_data['id'],
                            defaults=variant_defaults
                        )
                    else:
                        variant, v_created = Variant.objects.update_or_create(
                            sku=v_data['sku'],
                            defaults=variant_defaults
                        )
                    
                    # Ensure inventory exists
                    Inventory.objects.get_or_create(variant=variant)

                    # Handle Variant Images
                    for img_rel_path in v_data.get('variant_images', []):
                        img_full_path = os.path.join(base_dir, img_rel_path)
                        if os.path.exists(img_full_path):
                            with open(img_full_path, 'rb') as f:
                                django_file = File(f)
                                filename = os.path.basename(img_rel_path)
                                if not VariantImage.objects.filter(variant=variant, image__icontains=filename).exists():
                                    vi = VariantImage(variant=variant)
                                    vi.image.save(filename, django_file, save=True)

        self.stdout.write(self.style.SUCCESS('Successfully seeded products.'))
