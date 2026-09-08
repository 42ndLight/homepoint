# tasks.py

import boto3
from celery import shared_task
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError
import requests
from django.core.files.base import ContentFile

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
    if model_type == "product":
        model_class = ProductImage
    elif model_type == "variant":
        model_class = VariantImage
    else:
        return "Unsupported model path variant."

    try:
        obj = model_class.objects.get(pk=image_id)
    except model_class.DoesNotExist:
        return f"Image record {image_id} went missing."

    if obj.optimization_status == 'done' and obj.optimized_url:
        return f"Object {image_id} processing skip lock caught."

    obj.optimization_status = 'processing'
    obj.save(update_fields=['optimization_status'])

    try:
        # Prefer a directly accessible stored file before falling back to its URL.
        if obj.local_image and obj.local_image.name:
            image_source = obj.local_image
        elif obj.raw_external_url:
            image_source = obj.raw_external_url
        else:
            raise ValueError(
                f"No local image or external URL found for image record {image_id}."
            )

        optimized_io = optimize_and_resize_image(
            image_source=image_source,
            max_width=800,
            quality=78
        )

        # 2. Save result to local_image field (defined in ImageOptimizationMixin)
        filename = f"{obj.pk}_optimized.webp"
        obj.local_image.save(filename, ContentFile(optimized_io.getvalue()), save=False)
        
        # 3. Store generated URL and status
        obj.optimized_url = obj.local_image.url
        obj.optimization_status = 'done'
        obj.last_optimized_at = timezone.now()
        obj.error_log = None
        
        obj.save(update_fields=['local_image', 'optimized_url', 'optimization_status', 'last_optimized_at', 'error_log'])

        import os
        from django.conf import settings

        # After obj.save()
        absolute_path = os.path.join(settings.MEDIA_ROOT, obj.local_image.name)
        #print(f"[DEBUG] File written to disk: {absolute_path} | Exists: {os.path.exists(absolute_path)}")
        
        return f"Successfully optimized image ID: {image_id}"

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            obj.optimization_status = 'failed'
            obj.error_log = str(exc)
            obj.save(update_fields=['optimization_status', 'error_log'])
        
        raise exc