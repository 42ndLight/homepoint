import os
import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

# Import both image models
from ..models import ProductImage, VariantImage
from ..tasks import process_image_optimization_task

class UploadPipelineMixin:
    """
    Shared utilities for resolving dynamic Product vs Variant targets.
    """
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


class ImageUploadView(UploadPipelineMixin, APIView):
    """
    POST /api/products/upload/
    Accepts image file upload, saves it via default_storage, 
    creates the Image record, and triggers optimization task.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        uploaded_file = request.FILES['file']
        model_type, target_id, ImageModel, fk_field = self.resolve_target_context(request.data)

        if not target_id:
            return Response({"error": "Missing target_id (or product_id)"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not model_type:
            return Response({"error": "Invalid model_type. Must be 'product' or 'variant'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Generate a unique path for the uploaded image
            ext = os.path.splitext(uploaded_file.name)[1]
            relative_path = f"raw/{model_type}/{target_id}_{uuid.uuid4()}{ext}"
            
            # Use Django's default storage (which points to S3 if USE_AWS=True)
            saved_path = default_storage.save(relative_path, uploaded_file)
            
            # Get the public URL for the raw image
            raw_url = default_storage.url(saved_path)

            # Create the database record
            create_kwargs = {
                fk_field: target_id,
                'raw_external_url': raw_url,
                'optimization_status': 'pending'
            }
            img_obj = ImageModel.objects.create(**create_kwargs)
            
            # Trigger Celery task
            task = process_image_optimization_task.delay(img_obj.id, model_type=model_type)

            return Response({
                "message": f"{model_type.capitalize()} image uploaded successfully.",
                "url": raw_url,
                "task_id": task.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Error during image upload")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )