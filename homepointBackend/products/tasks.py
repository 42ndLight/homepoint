# tasks.py

import boto3
from celery import shared_task
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError
import requests

from .models import ProductImage, VariantImage
from .utils.image import optimize_and_resize_external_image

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(requests.RequestException, BotoCoreError, ClientError),
    retry_backoff=True
)
def process_image_optimization_task(self, image_id, model_type):
    # Dynamically grab active target model mapping pointer context
    if model_type == "product":
        model_class = ProductImage
    elif model_type == "variant":
        model_class = VariantImage
    else:
        # Extend tracking to variations easily here
        return "Unsupported model path variant."

    try:
        obj = model_class.objects.get(pk=image_id)
    except model_class.DoesNotExist:
        return f"Image record {image_id} went missing."

    # Idempotency lock execution skip check
    if obj.optimization_status == 'done' and obj.optimized_url:
        return f"Object {image_id} processing skip lock caught."

    # Mark active state processing mutation transition block
    obj.optimization_status = 'processing'
    obj.save(update_fields=['optimization_status'])

    try:
        # Download and run compression 
        optimized_io = optimize_and_resize_external_image(
            external_url=obj.raw_external_url,
            max_width=800,
            quality=78
        )

        # Pipe raw memory data target directly to structural AWS location setup
        from django.conf import settings
        from botocore.config import Config
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        target_s3_key = obj.get_s3_key()
        
        s3_client.upload_fileobj(
            Fileobj=optimized_io,
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=target_s3_key,
            ExtraArgs={
                'ContentType': 'image/webp',
                'CacheControl': 'max-age=31536000, public'
            }
        )

        # Successful save operations tracking updates execution blocks
        domain = settings.CLOUDFRONT_DOMAIN or f"{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
        obj.optimized_url = f"https://{domain}/{target_s3_key}"
        obj.optimization_status = 'done'
        obj.last_optimized_at = timezone.now()
        obj.error_log = None
        obj.save(update_fields=['optimized_url', 'optimization_status', 'last_optimized_at', 'error_log'])
        
        return f"Successfully optimized image ID: {image_id}"

    except Exception as exc:
        # Fallback tracking verification catch handles logic paths
        if self.request.retries >= self.max_retries:
            obj.optimization_status = 'failed'
            obj.error_log = str(exc)
            obj.save(update_fields=['optimization_status', 'error_log'])
        
        raise exc