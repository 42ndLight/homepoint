"""
Views for file upload and import status tracking.
"""

import os
from pathlib import Path
from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import ImportHistory
from .tasks import process_xlsx_import_task


def handle_file_upload(uploaded_file):
    """
    Save uploaded file to MEDIA_ROOT/uploads/ and return the path.
    """
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / uploaded_file.name
    with open(file_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    return str(file_path)


class FileImportView(APIView):
    """
    POST /api/files/
    Accepts XLSX file upload and triggers async Celery task.
    Returns 202 Accepted with task_id for polling.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # Validation: only .xlsx files
        if not uploaded_file.name.endswith('.xlsx'):
            return Response(
                {"error": "Only .xlsx files are accepted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validation: max 10 MB
        if uploaded_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File size exceeds 10 MB limit"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        try:
            # Save file
            file_path = handle_file_upload(uploaded_file)

            # Trigger Celery task
            task = process_xlsx_import_task.delay(file_path)

            # Create ImportHistory record
            ImportHistory.objects.create(
                task_id=task.id,
                status='PENDING',
                file_path=file_path
            )

            return Response(
                {
                    "task_id": task.id,
                    "status": "Processing Started"
                },
                status=status.HTTP_202_ACCEPTED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskStatusView(APIView):
    """
    GET /api/tasks/<task_id>/
    Returns the current status of an import task.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            history = ImportHistory.objects.get(task_id=task_id)
            return Response({
                "task_id": history.task_id,
                "status": history.status,
                "error_msg": history.error_msg,
                "created_at": history.created_at,
                "updated_at": history.updated_at,
            })
        except ImportHistory.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )
