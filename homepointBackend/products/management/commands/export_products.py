import json
import os
import time
import requests
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product, Variant
from supabase import create_client, Client

class Command(BaseCommand):
    help = 'Export product data and images for high-speed frontend/offline use or Vercel Blob storage / Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload',
            action='store_true',
            help='Upload the exported bundle to Vercel Blob (requires BLOB_READ_WRITE_TOKEN)',
        )
        parser.add_argument(
            '--supabase',
            action='store_true',
            help='Sync data to Supabase table',
        )
        parser.add_argument(
            '--folder',
            type=str,
            default='export_bundle',
            help='The output folder for the bundle',
        )

    def handle(self, *args, **kwargs):
        upload = kwargs['upload']
        sync_supabase = kwargs['supabase']
        output_folder = kwargs['folder']
        images_folder = os.path.join(output_folder, 'images')
        
        # Ensure folders exist
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(images_folder, exist_ok=True)

        self.stdout.write(f"Bundling data from {Product.objects.count()} products...")

        export_data = []
        products = Product.objects.prefetch_related('images', 'variants__images', 'category').all()
        
        for product in products:
            product_entry = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "category": product.category.name if product.category else "Uncategorized",
                "base_price": float(product.base_price),
                "product_images": [],
                "variants": []
            }

            # Process Product Gallery Images
            for img in product.images.all():
                if not img.image: continue
                filename = f"prod_{product.id}_{img.id}{os.path.splitext(img.image.name)[1]}"
                save_path = os.path.join(images_folder, filename)
                
                try:
                    shutil.copy(img.image.path, save_path)
                    product_entry["product_images"].append(f"images/{filename}")
                except Exception as e:
                    self.stderr.write(f"Failed to copy product image {img.id}: {str(e)}")
            
            # Process Variants
            for variant in product.variants.all():
                variant_data = {
                    "id": variant.id,
                    "sku": variant.sku,
                    "price": float(variant.price),
                    "unit_type": variant.unit_type,
                    "attributes": variant.attributes,
                    "variant_images": []
                }
                
                # Process Variant Images
                for img in variant.images.all():
                    if not img.image: continue
                    filename = f"var_{variant.sku}_{img.id}{os.path.splitext(img.image.name)[1]}"
                    save_path = os.path.join(images_folder, filename)
                    
                    try:
                        shutil.copy(img.image.path, save_path)
                        variant_data["variant_images"].append(f"images/{filename}")
                    except Exception as e:
                        self.stderr.write(f"Failed to copy variant image {img.id}: {str(e)}")
                
                product_entry["variants"].append(variant_data)
            
            export_data.append(product_entry)

        # Sync to Supabase if requested
        if sync_supabase:
            self.stdout.write("Syncing data to Supabase...")
            self.sync_to_supabase(export_data)

        # Save the JSON manifest with timestamp
        timestamp = int(time.time())
        manifest_filename = f'manifest_{timestamp}.json'
        manifest_path = os.path.join(output_folder, manifest_filename)
        with open(manifest_path, 'w') as f:
            json.dump(export_data, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f'Successfully bundled {len(export_data)} products to {output_folder}'))

        # Optional Vercel Blob Upload
        if upload:
            token = getattr(settings, 'VERCEL_BLOB_READ_WRITE_TOKEN', os.environ.get('VERCEL_BLOB_READ_WRITE_TOKEN'))
            # ... token check ...
            self.stdout.write("Uploading bundle to Vercel Blob...")
            
            # 1. Upload the TIMESTAMPED manifest (The real data)
            # This returns the unique URL that Vercel generates
            manifest_url = self.upload_to_vercel(manifest_path, f'products/{manifest_filename}', token)
            
            # 2. Upload images (Using fixed paths is fine for images)
            for img_file in os.listdir(images_folder):
                local_img_path = os.path.join(images_folder, img_file)
                self.upload_to_vercel(local_img_path, f'products/images/{img_file}', token)
            
            # 3. Create and upload the POINTER file (latest.json)
            # This tells the frontend where to find the newest manifest_url
            pointer_data = {
                "latest_manifest": manifest_url,
                "last_updated": timestamp
            }
            pointer_path = os.path.join(output_folder, 'latest.json')
            with open(pointer_path, 'w') as f:
                json.dump(pointer_data, f)
            
            # Crucial: Upload latest.json WITHOUT a random suffix so the URL stays stable
            # Note: You may need to add 'addRandomSuffix': 'false' to headers if using the API directly
            self.upload_to_vercel(pointer_path, 'products/latest.json', token)
            
        self.stdout.write(self.style.SUCCESS('Successfully uploaded bundle to Vercel Blob'))

    def upload_to_vercel(self, file_path, remote_filename, token):
        url = f"https://blob.vercel-storage.com/{remote_filename}"
        
        with open(file_path, 'rb') as f:
            headers = {
                'Authorization': f'Bearer {token}',
                'x-api-version': '1'
            }
            try:
                response = requests.put(url, data=f, headers=headers)
                if response.status_code == 200:
                    self.stdout.write(f"  Uploaded: {remote_filename}")
                else:
                    self.stderr.write(f"  Failed to upload {remote_filename}: {response.text}")
            except Exception as e:
                self.stderr.write(f"  Upload error for {remote_filename}: {str(e)}")

    def sync_to_supabase(self, data):
        url = getattr(settings, 'SUPABASE_URL', os.environ.get('SUPABASE_URL'))
        key = getattr(settings, 'SUPABASE_SERVICE_KEY', os.environ.get('SUPABASE_SERVICE_KEY'))

        if not url or not key:
            self.stderr.write("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
            return

        supabase: Client = create_client(url, key)

        try:
            # Upsert handles both inserting new records and updating existing ones based on 'id'
            # We use .upsert() assuming 'id' is your primary key
            # Note: Ensure the table name 'products' exists in your Supabase database
            response = supabase.table("products").upsert(data).execute()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully synced {len(data)} records to Supabase!"))
        except Exception as e:
            self.stderr.write(f"Supabase Sync Error: {str(e)}")
