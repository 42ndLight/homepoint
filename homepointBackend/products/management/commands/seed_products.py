import json
import os
import boto3
import re
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db import transaction
from django.conf import settings
from products.models import Category, Product, Variant, Inventory, ProductImage, VariantImage

class Command(BaseCommand):
    help = 'Seed products from manifest JSON (Local or S3)'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to manifest JSON file')
        parser.add_argument('--keep-ids', action='store_true', help='Keep the IDs from the JSON file')
        parser.add_argument('--s3', action='store_true', help='Read manifest and images from S3')
        parser.add_argument('--bucket', type=str, help='S3 Bucket name (defaults to AWS_STORAGE_BUCKET_NAME)')
        parser.add_argument('--prefix', type=str, default='export_bundle/', help='S3 prefix/folder to search in')

    def handle(self, *args, **options):
        file_path = options['file']
        keep_ids = options['keep_ids']
        use_s3 = options['s3']
        
        if use_s3:
            self.seed_from_s3(options)
        else:
            self.seed_from_local(file_path, keep_ids)

    def find_local_manifest(self, search_path=None):
        """Searches for manifest_*.json or manifest-*.json in common locations."""
        search_dirs = [
            '.', 
            'export_bundle', 
            'homepointBackend/export_bundle',
            '../export_bundle'
        ]
        if search_path:
            search_dirs.insert(0, search_path)

        for d in search_dirs:
            if not os.path.exists(d):
                continue
            
            # Look for manifest_*.json or manifest-*.json
            files = [f for f in os.listdir(d) if (f.startswith('manifest_') or f.startswith('manifest-')) and f.endswith('.json')]
            if files:
                files.sort() # Get the latest by name/timestamp
                return os.path.join(d, files[-1])
        return None

    def seed_from_local(self, file_path, keep_ids):
        if not file_path:
            file_path = self.find_local_manifest()
        else:
            # If user provided a path, check it directly first
            if not os.path.exists(file_path):
                 # Fallback: maybe they provided just the filename and it's in a subfolder
                 found = self.find_local_manifest(search_path=os.path.dirname(file_path) if os.path.dirname(file_path) else None)
                 if found and os.path.basename(found) == os.path.basename(file_path):
                     file_path = found

        if not file_path or not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Manifest file not found locally. Searched for: {file_path if file_path else "default manifest patterns"}'))
            # Print current directory to help debug Docker paths
            self.stdout.write(f"Current working directory: {os.getcwd()}")
            self.stdout.write(f"Files in current directory: {os.listdir('.')}")
            return
        
        if os.path.isdir(file_path):
            self.stdout.write(self.style.ERROR(f"Error: '{file_path}' is a directory, not a file. Please provide the path to the manifest JSON file."))
            return

        self.stdout.write(self.style.SUCCESS(f'Seeding from local file: {file_path}...'))
        base_dir = os.path.dirname(file_path)

        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.process_data(data, keep_ids, source_type='local', base_path=base_dir)

    def seed_from_s3(self, options):
        bucket_name = options['bucket'] or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        prefix = options['prefix']
        
        if not bucket_name:
            self.stdout.write(self.style.ERROR('S3 Bucket name not provided and AWS_STORAGE_BUCKET_NAME not set.'))
            return

        s3 = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )

        # Find latest manifest in S3
        self.stdout.write(f"Searching for manifest in S3 bucket '{bucket_name}' with prefix '{prefix}'...")
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        manifest_keys = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                filename = os.path.basename(key)
                if (filename.startswith('manifest_') or filename.startswith('manifest-')) and filename.endswith('.json'):
                    manifest_keys.append(key)
        
        if not manifest_keys:
            self.stdout.write(self.style.ERROR('No manifest found in S3.'))
            return
        
        manifest_keys.sort()
        latest_manifest_key = manifest_keys[-1]
        self.stdout.write(self.style.SUCCESS(f"Found manifest in S3: {latest_manifest_key}"))

        # Download manifest
        obj = s3.get_object(Bucket=bucket_name, Key=latest_manifest_key)
        data = json.loads(obj['Body'].read().decode('utf-8'))
        
        s3_base_prefix = os.path.dirname(latest_manifest_key)
        self.process_data(data, options['keep_ids'], source_type='s3', s3_client=s3, bucket=bucket_name, base_path=s3_base_prefix)

    def process_data(self, data, keep_ids, source_type='local', s3_client=None, bucket=None, base_path=''):
        with transaction.atomic():
            for item in data:
                category_name = item.get('category', 'Uncategorized')
                category, _ = Category.objects.get_or_create(name=category_name)

                product_defaults = {
                    'name': item['name'],
                    'description': item['description'],
                    'category': category,
                    'base_price': item['base_price'],
                }
                
                if keep_ids:
                    product, created = Product.objects.update_or_create(id=item['id'], defaults=product_defaults)
                else:
                    product, created = Product.objects.update_or_create(slug=item['slug'], defaults=product_defaults)
                
                self.stdout.write(f"{'Created' if created else 'Updated'} product: {product.name}")

                # Images for Product
                for img_rel_path in item.get('product_images', []):
                    self.save_image(product, img_rel_path, source_type, s3_client, bucket, base_path, is_variant=False)

                # Variants
                for v_data in item.get('variants', []):
                    variant_defaults = {
                        'product': product,
                        'price': v_data['price'],
                        'unit_type': v_data.get('unit_type', 'piece'),
                        'attributes': v_data.get('attributes', {}),
                        'item_code': v_data.get('item_code', ''),
                        'tax_type': v_data.get('tax_type', 'A'),
                    }
                    
                    if keep_ids:
                        variant, v_created = Variant.objects.update_or_create(id=v_data['id'], defaults=variant_defaults)
                    else:
                        variant, v_created = Variant.objects.update_or_create(sku=v_data['sku'], defaults=variant_defaults)
                    
                    Inventory.objects.get_or_create(variant=variant)

                    # Images for Variant
                    for img_rel_path in v_data.get('variant_images', []):
                        self.save_image(variant, img_rel_path, source_type, s3_client, bucket, base_path, is_variant=True)

        self.stdout.write(self.style.SUCCESS('Successfully seeded products.'))

    def save_image(self, instance, img_rel_path, source_type, s3_client, bucket, base_path, is_variant=False):
        filename = os.path.basename(img_rel_path)
        
        # Check if already exists to avoid duplicates
        if is_variant:
            if VariantImage.objects.filter(variant=instance, image__icontains=filename).exists():
                return
        else:
            if ProductImage.objects.filter(product=instance, image__icontains=filename).exists():
                return

        try:
            if source_type == 'local':
                full_path = os.path.join(base_path, img_rel_path)
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        django_file = File(f)
                        if is_variant:
                            vi = VariantImage(variant=instance)
                            vi.image.save(filename, django_file, save=True)
                        else:
                            pi = ProductImage(product=instance)
                            pi.image.save(filename, django_file, save=True)
            
            elif source_type == 's3':
                s3_key = f"{base_path}/{img_rel_path}".replace('//', '/')
                try:
                    obj = s3_client.get_object(Bucket=bucket, Key=s3_key)
                    django_file = File(BytesIO(obj['Body'].read()))
                    if is_variant:
                        vi = VariantImage(variant=instance)
                        vi.image.save(filename, django_file, save=True)
                    else:
                        pi = ProductImage(product=instance)
                        pi.image.save(filename, django_file, save=True)
                except s3_client.exceptions.NoSuchKey:
                    self.stdout.write(self.style.WARNING(f"Image not found in S3: {s3_key}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saving image {filename}: {str(e)}"))
