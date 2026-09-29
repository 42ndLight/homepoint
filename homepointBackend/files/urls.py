from django.urls import path
from .views import FileImportView, TaskStatusView
from .services import PresignedUploadView, ConfirmUploadView

app_name = 'files'

urlpatterns = [
    path('files/', FileImportView.as_view(), name='file-import'),
    path('tasks/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('uploads/presign/', PresignedUploadView.as_view(), name='presign-upload'),
    path('uploads/<uuid:record_id>/confirm/', ConfirmUploadView.as_view(), name='confirm-upload'),
]
