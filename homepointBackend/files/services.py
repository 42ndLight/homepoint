import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.conf import settings

from .models import PendingUpload, ImportHistory
from .tasks import process_xlsx_import_task
from products.models import ProductImage, VariantImage
from products.tasks import process_image_optimization_task

class PresignedUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        kind = request.data.get('kind')
        content_type = request.data.get('content_type')
        target_id = request.data.get('target_id')

        if kind not in ["product_image", "variant_image", "xlsx_import"]:
            return Response({"error": "Invalid kind"}, status=status.HTTP_400_BAD_REQUEST)

        if kind == "xlsx_import" and content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return Response({"error": "Invalid content type for xlsx"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a unique storage key
        record_id = uuid.uuid4()
        
        ext = "xlsx" if kind == "xlsx_import" else "jpg"
        if content_type == "image/png":
            ext = "png"
        elif content_type == "image/webp":
            ext = "webp"
        
        if kind == "xlsx_import":
            key = f"uploads/{record_id}.{ext}"
        else:
            # images
            target_str = target_id or "unknown"
            key = f"raw/{kind.split('_')[0]}/{target_str}_{record_id}.{ext}"

        # Generate presigned POST using boto3 if S3 storage is configured
        try:
            # In Django, if default_storage is S3, it has connection.meta.client
            client = default_storage.connection.meta.client
            bucket = default_storage.bucket_name
            # The URL will force content-length-range to 10MB
            presigned_data = client.generate_presigned_post(
                Bucket=bucket,
                Key=key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 0, 10485760]  # 10 MB max
                ],
                ExpiresIn=3600
            )
        except Exception as e:
            # Fallback if not S3 or error
            import logging
            logging.getLogger(__name__).error(f"Error generating presigned post: {e}")
            return Response({"error": "Could not generate presigned url"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        PendingUpload.objects.create(
            record_id=record_id,
            storage_key=key,
            kind=kind,
            target_id=target_id,
            status='pending'
        )

        return Response({
            "record_id": str(record_id),
            "url": presigned_data["url"],
            "fields": presigned_data["fields"]
        })

class ConfirmUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, record_id):
        try:
            pending = PendingUpload.objects.get(record_id=record_id)
        except PendingUpload.DoesNotExist:
            return Response({"error": "Upload record not found"}, status=status.HTTP_404_NOT_FOUND)

        if pending.status != 'pending':
            return Response({"error": "Upload already processed"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify it actually landed
        if not default_storage.exists(pending.storage_key):
            return Response({"error": "File not found in bucket"}, status=status.HTTP_404_NOT_FOUND)

        pending.status = 'uploaded'
        pending.save()

        # Enqueue existing tasks
        if pending.kind == "xlsx_import":
            task_id = str(uuid.uuid4())
            ImportHistory.objects.create(
                task_id=task_id,
                status='PENDING',
                file_path=pending.storage_key
            )
            process_xlsx_import_task.apply_async(args=[pending.storage_key], task_id=task_id)
            return Response({"message": "Upload confirmed, processing started", "task_id": task_id})
        else:
            model_type = "product" if pending.kind == "product_image" else "variant"
            ImageModel = ProductImage if model_type == "product" else VariantImage
            fk_field = "product_id" if model_type == "product" else "variant_id"

            raw_url = default_storage.url(pending.storage_key)
            create_kwargs = {
                fk_field: pending.target_id,
                'raw_external_url': raw_url,
                'raw_storage_key': pending.storage_key,
                'optimization_status': 'pending'
            }
            img_obj = ImageModel.objects.create(**create_kwargs)
            task = process_image_optimization_task.delay(img_obj.id, model_type=model_type)
            return Response({"message": "Upload confirmed, optimization started", "task_id": task.id, "image_id": img_obj.id})
