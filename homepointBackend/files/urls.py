from django.urls import path
from .views import FileImportView, TaskStatusView

app_name = 'files'

urlpatterns = [
    path('files/', FileImportView.as_view(), name='file-import'),
    path('tasks/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
]
