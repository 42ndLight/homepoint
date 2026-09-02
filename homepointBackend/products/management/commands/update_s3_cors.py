import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Updates the CORS policy for the S3/T3 storage bucket'

    def handle(self, *args, **options):
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL
        )
        
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'HEAD'],
                'AllowedOrigins': [
                    'https://homepoint-pi.vercel.app',
                    'http://localhost:5173'  # For local frontend development
                ],
                'ExposeHeaders': ['ETag']
            }]
        }
        
        s3.put_bucket_cors(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        
        self.stdout.write(self.style.SUCCESS("CORS updated successfully on Railway bucket!"))
