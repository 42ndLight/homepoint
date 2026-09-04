# tasks.py

import boto3
from celery import shared_task
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError
import requests

from .models import ProductImage, VariantImage
from .utils.image import optimize_and_resize_image

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
        raw_file = obj.image.open('rb')

        # Download and run compression 
        optimized_io = optimize_and_resize_image(
            external_url=obj.raw_external_url,
            max_width=800,
            quality=78
        )

        # Save locally too for dual support
        from django.core.files.base import ContentFile
        filename = f"{obj.pk}_optimized.webp"
        obj.optimized_image.save(filename, ContentFile(optimized_io.getvalue()), save=False)
        
        # Grab the storage-generated public/S3 URL
        obj.optimized_url = obj.optimized_image.url
        obj.optimization_status = 'done'
        obj.last_optimized_at = timezone.now()
        obj.error_log = None
        
        obj.save(update_fields=['optimized_image', 'optimized_url', 'optimization_status', 'last_optimized_at', 'error_log'])
        
        return f"Successfully optimized image ID: {image_id}"

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            obj.optimization_status = 'failed'
            obj.error_log = str(exc)
            obj.save(update_fields=['optimization_status', 'error_log'])
        
        raise exc