import boto3
from botocore.config import Config
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Import both image models
from ..models import ProductImage, VariantImage
from ..tasks import process_image_optimization_task


class UploadPipelineMixin:
    """
    Shared utilities for modernizing the S3 client configuration, 
    and resolving dynamic Product vs Variant targets dynamically.
    """
    def get_s3_client(self):
        endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        addressing_style = getattr(settings, 'AWS_S3_ADDRESSING_STYLE', 'virtual')

        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=endpoint_url,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': addressing_style}
                )
        )

    def resolve_target_context(self, data):
        """
        Dynamically figures out if we're targeting a product or a variant.
        Returns: (model_type, target_id, ImageModel, fk_field_name)
        """
        model_type = data.get('model_type', 'product').lower()
        # Fallback to legacy 'product_id' if target_id isn't explicitly passed
        target_id = data.get('target_id') or data.get('product_id')
        
        if model_type not in ['product', 'variant']:
            return None, None, None, None
            
        mappings = {
            'product': (ProductImage, 'product_id'),
            'variant': (VariantImage, 'variant_id')
        }
        ImageModel, fk_field = mappings[model_type]
        return model_type, target_id, ImageModel, fk_field


class PresignedUrlGenerationView(UploadPipelineMixin, APIView):
    """
    Step 1: Client tells Django: 'I want to upload X images for target Y'
    Hands back unique target keys and authenticated temporary S3 links.
    Supports both products and variants seamlessly.
    """
    def post(self, request):
        file_names = request.data.get('filenames', [])
        content_types = request.data.get('content_types', [])
        model_type, target_id, _, _ = self.resolve_target_context(request.data)
        
        if not target_id or not file_names:
            return Response({"error": "Missing target_id (or product_id) or filenames list"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not model_type:
            return Response({"error": "Invalid model_type. Must be 'product' or 'variant'."}, status=status.HTTP_400_BAD_REQUEST)

        s3_client = self.get_s3_client()
        presigned_data = []
        timestamp = timezone.now().timestamp()
        
        for idx, name in enumerate(file_names):
            # Build an explicit directory layout depending on the model context type
            clean_name = f"raw/{model_type}/{target_id}_{timestamp}_{name}"
            file_content_type = content_types[idx] if idx < len(content_types) else 'image/jpeg'
            
            try:
                presigned_url = s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': clean_name,
                        'ContentType': file_content_type,
                    },
                    ExpiresIn=3600
                )
                presigned_data.append({
                    "original_name": name,
                    "target_key": clean_name,
                    "upload_url": presigned_url
                })
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response({"uploads": presigned_data}, status=status.HTTP_200_OK)


class InventoryUploadFinalizeView(UploadPipelineMixin, APIView):
    """
    Step 2: Client successfully pushed raw bytes to S3 directly.
    They ping this view with the raw keys to queue async pipeline processing.
    """
    def post(self, request):
        uploaded_keys = request.data.get('keys', [])
        model_type, target_id, ImageModel, fk_field = self.resolve_target_context(request.data)

        if not target_id or not uploaded_keys:
            return Response({"error": "Missing target_id (or product_id) or keys list"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not model_type:
            return Response({"error": "Invalid model_type. Must be 'product' or 'variant'."}, status=status.HTTP_400_BAD_REQUEST)

        created_task_ids = []
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        region = settings.AWS_S3_REGION_NAME
        endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        addressing_style = getattr(settings, 'AWS_S3_ADDRESSING_STYLE', 'virtual')

        for key in uploaded_keys:
            if endpoint_url:
                # Extract scheme (e.g. 'https://') and base host
                scheme, host = endpoint_url.split("://")
                
                if addressing_style == 'virtual':
                    # Virtual host format: https://bucket.s3-provider.com/key
                    raw_url = f"{scheme}://{bucket}.{host.rstrip('/')}/{key}"
                else:
                    # Path style format: https://s3-provider.com/bucket/key
                    raw_url = f"{scheme}://{host.rstrip('/')}/{bucket}/{key}"
            else:
                region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
                raw_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
            
            # Use dynamic unpacking to assign either product_id or variant_id
            create_kwargs = {
                fk_field: target_id,
                'raw_external_url': raw_url,
                'optimization_status': 'pending'
            }
            img_obj = ImageModel.objects.create(**create_kwargs)
            
            # Send the model_type down to Celery so it knows which pipeline to execute
            task = process_image_optimization_task.delay(img_obj.id, model_type=model_type)
            created_task_ids.append(task.id)

        return Response({
            "message": f"{model_type.capitalize()} images tracked successfully. Pipeline workers triggered.",
            "task_ids": created_task_ids
        }, status=status.HTTP_202_ACCEPTED)