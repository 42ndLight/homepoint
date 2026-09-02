import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Updates the CORS policy for the S3/T3 storage bucket'

    def handle(self, *args, **options):
        aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)

        if not all([aws_access_key_id, aws_secret_access_key, bucket_name]):
            self.stdout.write(self.style.ERROR("AWS settings (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME) are not fully configured."))
            return

        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url
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
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        
        self.stdout.write(self.style.SUCCESS("CORS updated successfully on Railway bucket!"))
